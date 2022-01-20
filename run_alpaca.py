import alpaca_trade_api as alpaca
from jinja2 import Environment, FileSystemLoader, select_autoescape

from configparser import ConfigParser
from argparse import ArgumentParser
import datetime
from time import sleep
from typing import Dict, List
import math
import logging as log
import os.path
import time

import cmErrors
from utils.file_utils import loadStratFile, loadStockFile
from utils.api_utils import loadAPI, getSetupBars
from objects.action import *
from objects.stock import *
from strategies.strategy import *
from strategies.hardStrategy import HardStrategy
from utils.emailer import CMEmailer


def toTS(t):
    return t.replace(tzinfo=datetime.timezone.utc).timestamp()


BUY_PWR_SAFETY = 0.985

MARKET_CLOSE_DELTA = 15 * 60


def calcQty(buyPwr: float, cost: float):
    return math.floor(buyPwr / cost)


class Trader:
    def __init__(self, strats: Dict[str, Strategy], api: alpaca.REST, emailer: CMEmailer, cashOnly: bool = False):
        self.api = api
        self.emailer = emailer
        self.htmlEnv = Environment(
            loader=FileSystemLoader('html_templates'),
            autoescape=select_autoescape()
        )
        self.emailTemplate = self.htmlEnv.get_template("emailtemplate.html")

        self.cashOnly = cashOnly

        # TODO check for proper shutdown

        # First cancel any existing orders?
        self.api.cancel_all_orders()
        # Close all positions?
        # self.api.close_all_positions()

        # setup initial buying power
        self.buyPwr = 0
        self.updateBuyPwr()

        self.prevEquity = round(float(self.api.get_account().equity), 2)

        # Internal day counter
        self.tradeDay = 0

        # Dict of symb->strat
        self.strats = strats

        # Dict of symb->stock
        self.stocks = {}
        for x in self.strats.keys():
            self.stocks[x] = Stock(x)

        setupTime = max([x.getSetupTime() for x in strats.values()])

        setupBars = getSetupBars(self.api, setupTime, list(self.strats.keys()))

        # Setup Indicators
        for sym, strat in strats.items():
            strat.setupIndicators(setupBars[sym])

        # If market is closed, get current day
        if not self.api.get_clock().is_open:
            self.updateIndicators()

        # Dict of order.id -> order
        self.openOrders = {}
        # List of trades to send in next update
        self.trades = []


    def run(self):
        try:
            while True:
                # Inc trade day
                self.tradeDay += 1
                log.info(f'Begin Trade Day: {self.tradeDay}')

                clock = self.clock()
                nextclose = toTS(clock.next_close)

                # wait for 15min before close
                log.info('Waiting for 15min before close')
                self.waitForTS(nextclose - MARKET_CLOSE_DELTA)

                # Update indicators with today's values
                log.info('Updating Indicators')
                self.updateIndicators()

                # Update positions and BP
                log.info('Updating Positions')
                self.updatePositions()
                self.updateBuyPwr()

                # Calculate today's actions
                log.info('Calculating Daily Actions')
                actions = self.getDailyActions()

                # Run actions
                log.info('Running Daily Actions')
                self.runActions(actions)

                # Wait for 1min after the market to close
                log.info('Waiting for 1min after close')
                self.waitForTS(nextclose + 60)

                # Update positions and BP
                log.info('Updating Positions')
                self.updatePositions()
                self.updateBuyPwr()
                self.updateTrades()

                # Send update email
                log.info('Sending Update Email')
                self.sendUpdate(actions)

                # Force wait till morning
                log.info('Waiting until next open')
                nextOpen = toTS(self.clock().next_open)
                self.waitForTS(nextOpen + 60)


        except cmErrors.CMError as err:
            log.critical(err)
        except KeyboardInterrupt:
            pass

        log.info('Stopping System, Cancelling all existing orders')
        self.api.cancel_all_orders()
        # Close all positions?
        # self.api.close_all_positions()
        log.info('Done')

    def updateIndicators(self):
        snaps = self.api.get_snapshots(list(self.stocks.keys()))

        for sym, stk in self.stocks.items():
            stk.updateBar(snaps[sym].daily_bar)
            bar = stk.bar
            self.strats[sym].addData(bar.l, bar.c, bar.h)

    def updateTrades(self):
        filled = []
        for orderid in self.openOrders:
            order = self.api.get_order(orderid)

            if order.status == 'filled':
                filled.append(orderid)

                qty = int(order.filled_qty)
                price = float(order.filled_avg_price)
                value = qty * price

                t = {
                    'symbol': order.symbol,
                    'side': order.side,
                    'qty': qty,
                    'price': price,
                    'value': value
                }

                self.trades.append(t)

        for x in filled:
            self.openOrders.pop(x)

    def updatePositions(self):
        positions = self.api.list_positions()
        openset = set()
        for p in positions:
            openset.add(p.symbol)

            self.stocks[p.symbol].position = p

        closed = self.stocks.keys() - openset
        for s in closed:
            self.stocks[s].position = None


    def position(self, stock: Stock):
        return self.api.get_position(stock.symbol)

    def updateBuyPwr(self):
        info = self.api.get_account()
        self.buyPwr = round(float(info.buying_power) * BUY_PWR_SAFETY, 2)

    def getDailyActions(self) -> List[Action]:
        actions = []
        for sym, strat in self.strats.items():
            stk = self.stocks[sym]
            actions.append(strat.nextAction(self.tradeDay, stk))

        return actions

    def runActions(self, actions: List[Action]):
        numOutOfMarket = 0
        for sym, stock in self.stocks.items():
            if stock.status() == StockStatus.OutMarket:
                numOutOfMarket += 1

        buyPwr = self.buyPwr / numOutOfMarket

        for a in actions:
            if a.action == ActionEnum.Buy:
                self.submitBuy(a, buyPwr)
            elif a.action == ActionEnum.BuyAndStop:
                self.submitBuyAndStop(a, buyPwr)
            elif a.action == ActionEnum.Sell:
                self.submitSell(a)
            elif a.action == ActionEnum.UpdateStop:
                self.submitUpdateStop(a)
            elif a.action == ActionEnum.Hold:
                # ILB
                pass

            log.info(str(a))

    def submitBuy(self, action: Action, buyPwr):
        qty = calcQty(buyPwr, action.stock.bar.c)

        order = self.api.submit_order(
            symbol=action.stock.symbol,
            qty=qty,
            side='buy',
            type='market',
            time_in_force='day'
        )

        action.stock.order = order
        action.stock.stopOrder = None
        self.openOrders[order.id] = order

    def submitBuyAndStop(self, action: Action, buyPwr):
        qty = calcQty(buyPwr, action.stock.bar.c)

        try:
            order = self.api.submit_order(
                symbol=action.stock.symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='day',

                # Class: One-Triggers-Other, activates the stop loss after buy is filled
                order_class='oto',
                stop_loss={
                    'stop_price': action.args['stopPrice'],
                    'limit_price': action.args['limitPrice']
                }
            )

            action.stock.order = order
            action.stock.stopOrder = order.legs[0]
            self.openOrders[order.id] = order
            self.openOrders[order.legs[0].id] = order.legs[0]

        except KeyError as err:
            raise cmErrors.ActionError(f'Action missing argument: "{str(err)}", Action: {str(action)}')
        except alpaca.rest.APIError:
            raise

    def submitSell(self, action: Action):
        """
        try:
            order = self.api.submit_order(
                symbol=action.symbol,
                qty=action.args['qty'],
                side='sell',
                type='market',
                time_in_force='day',
            )
        except KeyError as err:
            raise cmErrors.ActionError(f'Action missing argument: "{str(err)}", Action: {str(action)}')
        except alpaca.rest.APIError:
            # error submitting order
            pass
        """

        try:
            order = self.api.close_position(symbol=action.stock.symbol)
            action.stock.order = None
            action.stock.stopOrder = None
            action.stock.lastCloseOrder = order
            self.openOrders[order.id] = order
        except alpaca.rest.APIError:
            raise

    def submitUpdateStop(self, action: Action):
        try:
            if action.stock.stopOrder is None:
                raise cmErrors.ActionError('Cannot Update stop, no stop created')

            order = self.api.replace_order(order_id=action.stock.stopOrder.id,
                                           stop_price=action.args['stopPrice'],
                                           limit_price=action.args['limitPrice'])

            action.stock.stopOrder = order
        except KeyError as err:
            raise cmErrors.ActionError(f'Action missing argument: "{str(err)}", Action: {str(action)}')
        except alpaca.rest.APIError:
            raise

    def sendUpdate(self, actions: List[Action]):
        acts = {}
        for a in actions:
            acts[a.stock.symbol] = a

        header = f'Stock Algo Daily Update: {datetime.datetime.today()}'

        info = self.api.get_account()

        curEquity = round(float(info.equity), 2)
        totalPL = curEquity - self.prevEquity

        positions = []
        for sym, s in self.stocks.items():
            if s.position is not None:
                p = {
                    'symbol': s.symbol,
                    'qty': s.position.qty,
                    'pl': s.position.unrealized_pl,
                    'price': s.position.current_price,
                    'value': s.position.market_value,
                    'p_value': s.position.avg_entry_price,
                    'p_date': s.order.filled_at,
                    'stop_price': s.stopOrder.stop_price,
                    'last_stop': s.lastStopUpdate,
                    'next_stop': s.nextStopUpdate
                }
                positions.append(p)

        content = self.emailTemplate.render(
            portfolio_start=self.prevEquity,
            portfolio_cur=curEquity,
            portfolio_pl=totalPL,
            trades=self.trades,
            postions=positions
        )

        self.emailer.send(header, content)
        self.prevEquity = curEquity
        self.trades = []



    def clock(self) -> alpaca.rest.Clock:
        """Shorcut to get the API clock"""
        return self.api.get_clock()

    def waitForTS(self, ts):
        """Utility to wait until timestamp"""

        while True:
            clock = self.clock()
            diff = ts - toTS(clock.timestamp)
            if diff <= 0:
                return

            if diff > 6:
                log.info(f'Waiting {diff / 60:.2f}min')
                timeToSleep = diff - 5
                sleep(timeToSleep)
            else:
                sleep(2)


def runTrader(*, stratFile: str = None, stockFile: str = None, liveRun: bool = False,
              stocks: List[str] = None, stratVars=None):
    config = ConfigParser()
    config.read(r'config/system.cfg')

    logname = time.strftime(r'%Y_%b_%dT%H_%M_%S')

    if not os.path.exists('logs'):
        os.mkdir('logs')

    log.basicConfig(
        filename=f'logs/{logname}.txt',
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt=r'%Y-%m-%d %H:%M:%S',
        filemode='w',
        level=log.INFO
    )

    console = log.StreamHandler()
    console.setFormatter(log.Formatter('%(message)s'))
    console.setLevel(log.INFO)
    log.getLogger("").addHandler(console)

    apiCfg = config['Alpaca']

    api = loadAPI(apiCfg, liveRun)
    if api is None:
        log.info('System Exitting')
        return

    if stratFile is not None:
        log.info('Loading Strategy')
        stratVars = loadStratFile(stratFile)

    if stockFile is not None:
        log.info('Loading Stocks')
        stocks = loadStockFile(stockFile)

    strats = {}
    for sym in stocks:
        strats[sym] = HardStrategy(sym, stratVars)

    emailer = CMEmailer(config['Email'])

    trader = Trader(strats, api, emailer)
    trader.run()


def main():
    parser = ArgumentParser()

    parser.add_argument('-s', '--strat', required=True)
    parser.add_argument('-stx', '--stocks', required=True)
    parser.add_argument('--liveRun', action='store_true')
    # parser.add_argument('-c', '--cashOnly', action='store_true')

    args = parser.parse_args()
    runTrader(stratFile=args.strat, stockFile=args.stocks, liveRun=args.liveRun)


if __name__ == '__main__':
    main()
