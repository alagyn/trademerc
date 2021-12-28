import alpaca_trade_api as alpaca
from alpaca_trade_api.common import URL
from alpaca_trade_api import TimeFrame, TimeFrameUnit

from dotenv import dotenv_values
from argparse import ArgumentParser
import datetime
from time import sleep
import signal
from typing import Dict, List
import math
import logging as log
import os.path
import time

import cmErrors
from backtester import loadStratFile, loadStockFile
from indicators.indicator import IndicatorManager
from stock import *
from strategies.strategy import *
from strategies.hardStrategy import HardStrategy
from emailer import CMEmailer

NEED_TO_STOP = False


def toTS(t):
    return t.replace(tzinfo=datetime.timezone.utc).timestamp()


DATE_FMT = r'%Y-%m-%d'
BUY_PWR_SAFETY = 0.985

MARKET_CLOSE_DELTA = 15 * 60


def calcSetupStartDate(endDay, setupTime):
    out = endDay
    while setupTime >= 0 or out.weekday() >= 5:
        out -= datetime.timedelta(1)
        if out.weekday() < 5:
            setupTime -= 1

    return out


class Trader:
    def __init__(self, strats: Dict[str, Strategy], api: alpaca.REST, emailer: CMEmailer, cashOnly: bool = False):
        self.api = api
        self.emailer = emailer
        self.cashOnly = cashOnly

        # First cancel any existing orders?
        self.api.cancel_all_orders()
        # Close all positions?
        # self.api.close_all_positions()

        self.iManage = IndicatorManager()

        # setup initial buying power
        self.buyPwr = 0
        self.updateBuyPwr()

        # Internal day counter
        self.tradeDay = 0

        # Dict of symb->strat
        self.strats = strats

        # Dict of symb->stock
        self.stocks = {}

        setupTime = self.iManage.getSetupTime()

        setupBars = {}

        endSetupDay = datetime.datetime.today()

        # if market is open, only get up to yesterday
        if self.clock().is_open:
            endSetupDay -= datetime.timedelta(1)

        startSetupDay = calcSetupStartDate(endSetupDay, setupTime)

        startSetupStr = startSetupDay.strftime(DATE_FMT)
        endSetupStr = endSetupDay.strftime(DATE_FMT)
        actualSetup = 0
        for x in strats.keys():
            stock = Stock(x)

            self.stocks[x] = stock
            setupBars[x] = self.api.get_bars(symbol=x,
                                             timeframe=TimeFrame(1, TimeFrameUnit.Day),
                                             start=startSetupStr,
                                             end=endSetupStr,
                                             adjustment='raw').df
            actualSetup = len(setupBars[x])

        if actualSetup < setupTime:
            raise cmErrors.NotSetupError()

        # Setup Indicators
        for i in range(actualSetup):
            for x in setupBars:
                low = setupBars[x]['low'][i]
                close = setupBars[x]['close'][i]
                high = setupBars[x]['high'][i]

                self.iManage.addData(x, low, close, high)

    def run(self):
        global NEED_TO_STOP

        try:
            while not NEED_TO_STOP:
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

                # Send update email
                log.info('Sending Update Email')
                self.sendDailyUpdate(actions)

                # Force wait till morning
                log.info('Waiting until next open')
                nextOpen = toTS(self.clock().next_open)
                self.waitForTS(nextOpen + 60)


        except cmErrors.CMError as err:
            log.critical(err)
        except KeyboardInterrupt:
            pass

        log.info('Stopping System, Cancelling all existing order')
        self.api.cancel_all_orders()
        # Close all positions?
        # self.api.close_all_positions()
        log.info('Done')

    def updateIndicators(self):
        snaps = self.api.get_snapshots(list(self.stocks.keys()))

        for sym, stk in self.stocks.items():
            stk.updateBar(snaps[sym].daily_bar)
            bar = stk.bar
            self.iManage.addData(sym, bar.l, bar.c, bar.h)

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
            elif a.action == ActionEnum.Sell:
                self.submitSell(a)
            elif a.action == ActionEnum.UpdateStop:
                self.submitUpdateStop(a)
            elif a.action == ActionEnum.Hold:
                # ILB
                pass

            log.info(str(a))

    def submitBuy(self, action: Action, buyPwr):

        qty = math.floor(buyPwr / action.stock.bar.c)

        try:
            order = self.api.submit_order(
                symbol=action.stock.symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='day',

                # Class: One-Triggers-Other, activates the stop loss after buy goes through
                order_class='oto',
                stop_loss={
                    'stop_price': action.args['stopPrice'],
                    'limit_price': action.args['limitPrice']
                }
            )

            action.stock.order = order
            action.stock.stopOrder = order.legs[0]

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
            self.api.close_position(symbol=action.stock.symbol)
            action.stock.order = None
        except alpaca.rest.APIError:
            raise

    def submitUpdateStop(self, action: Action):
        try:
            order = self.api.replace_order(order_id=action.stock.stopOrder.id,
                                           stop_price=action.args['stopPrice'],
                                           limit_price=action.args['limitPrice'])

            action.stock.order = order
        except KeyError as err:
            raise cmErrors.ActionError(f'Action missing argument: "{str(err)}", Action: {str(action)}')
        except alpaca.rest.APIError:
            raise

    def sendDailyUpdate(self, actions: List[Action]):
        acts = {}
        for a in actions:
            acts[a.stock.symbol] = a

        header = f'Stock Algo Daily Update: {datetime.datetime.today()}'

        info = self.api.get_account()
        accountInfo = f'Account:\n'
        accountInfo += f'Buying Power: ${float(info.buying_power):.2f}\n\n'

        stkUpdates = ''
        for sym in sorted(self.strats.keys()):
            stkUpdates += f'Symbol: {sym}\n'
            stock = self.stocks[sym]

            if stock.position is None:
                stkUpdates += f'\tStatus: Out Of Market\n'
            else:
                stkUpdates += f'\tStatus: In Market\n'
                stkUpdates += f'\t\tEntry Price: ${stock.position.avg_entry_price:.2f}\n'
                stkUpdates += f'\t\tQty: {stock.position.qty}\n'
                stkUpdates += f'\t\tCurrent Total Market Value: ${stock.position.market_value}\n'
                stkUpdates += f'P/L: ${stock.position.unrealized_pl:.2f}, {stock.position.unrealized_plpc:.2%}\n'
                stkUpdates += f'Stop: ${stock.stopOrder.stop_price}, Limit: ${stock.stopOrder.limit_price}'

            stkUpdates += '\n'

            stkUpdates += f"\tToday's Action: {acts[sym].action.name}\n"
            for key, val in acts[sym].args.items():
                stkUpdates += f'\t\t{key}: {val}\n'

            stkUpdates += '\n'

        # TODO send open orders?

        content = accountInfo + stkUpdates
        self.emailer.send(header, content)

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


PAPER_ENDPOINT = 'https://paper-api.alpaca.markets'
LIVE_ENDPOINT = 'https://api.alpaca.markets'


def main():
    parser = ArgumentParser()

    parser.add_argument('-s', '--strat', required=True)
    parser.add_argument('-stx', '--stocks', required=True)
    parser.add_argument('--liveRun', action='store_true')
    # parser.add_argument('-c', '--cashOnly', action='store_true')

    args = parser.parse_args()

    config = dotenv_values('ignore/.env')
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

    if args.liveRun:
        x = input('Are you sure you want to run using the LIVE ACCOUNT? (YES/NO):')
        if x != 'YES':
            print('System Exiting')
            return
        else:
            log.info('Initializing Live Account')
            api_key = config['LIVE_API_KEY_ID']
            api_secret = config['LIVE_SECRET']
            endpoint = LIVE_ENDPOINT
    else:
        log.info('Initializing Paper Account')
        api_key = config['PAPER_API_KEY_ID']
        api_secret = config['PAPER_SECRET']
        endpoint = PAPER_ENDPOINT

    log.info('Loading Strategy')
    stratVars = loadStratFile(args.strat)['variables']

    log.info('Loading Stocks')
    stocks = loadStockFile(args.stocks)

    api = alpaca.REST(api_key, api_secret, URL(endpoint), 'v2')

    strats = {}
    for sym in stocks:
        strats[sym] = HardStrategy(sym, stratVars)

    emailer = CMEmailer(config)

    trader = Trader(strats, api, emailer)
    trader.run()


if __name__ == '__main__':

    main()
