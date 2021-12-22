import alpaca_trade_api as alpaca
import alpaca_trade_api.rest
from alpaca_trade_api.common import URL
from alpaca_trade_api import TimeFrame, TimeFrameUnit

from dotenv import dotenv_values
from argparse import ArgumentParser
import datetime
from threading import Thread
from time import sleep
import signal
from typing import Dict, List

import cmErrors
from backtester import loadStratFile, loadStockFile
from indicators.indicator import IndicatorManager
from stock import *
from strategies.strategy import *
from strategies.hardStrategy import HardStrategy
from emailer import CMEmailer

NEED_TO_STOP = False


def toTS(time):
    return time.replace(tzinfo=datetime.timezone.utc).timestamp()


DATE_FMT = r'%Y-%m-%d'
BUY_PWR_SAFETY = 0.9


class Trader:
    def __init__(self, strats: Dict[str, Strategy], api: alpaca.REST, emailer: CMEmailer):
        self.api = api
        self.emailer = emailer

        # First cancel any existing orders?
        self.api.cancel_all_orders()
        # Close all positions?
        # self.api.close_all_positions()

        self.iManage = IndicatorManager()

        info = self.api.get_account()

        # setup initial buying power
        initialBuyingPower = info.buying_power
        safeBuyingPwr = initialBuyingPower * BUY_PWR_SAFETY
        perstockBuyPwr = round(safeBuyingPwr / len(strats), 2)
        print(f'Total Buying Power: ${initialBuyingPower:.2f}\n'
              f'Safe Buying power at {BUY_PWR_SAFETY:.2%}%: ${safeBuyingPwr:.2f}\n'
              f'Buying power per stock with {len(strats)} stocks: ${perstockBuyPwr:.2f}')

        # Internal day counter
        self.tradeDay = 0

        # Dict of symb->strat
        self.strats = strats

        setupTime = self.iManage.getSetupTime()

        self.stocks = {}
        setupBars = {}

        endSetupDay = datetime.datetime.today()
        setupDelta = datetime.timedelta(setupTime + 1)
        startSetupDay = endSetupDay - setupDelta

        startSetupStr = startSetupDay.strftime(DATE_FMT)
        endSetupStr = endSetupDay.strftime(DATE_FMT)

        for x in strats.keys():
            stock = Stock(x)
            stock.buyPower = perstockBuyPwr
            stock.initBuyPower = perstockBuyPwr

            self.stocks[x] = stock
            setupBars[x] = self.api.get_bars(x, TimeFrame(1, TimeFrameUnit.Day),
                                             startSetupStr, endSetupStr, adjustment='raw').df
        # Setup Indicators
        for i in range(setupTime):
            for x in setupBars:
                low = setupBars[x]['low'][i]
                close = setupBars[x]['close'][i]
                high = setupBars[x]['high'][i]

                self.iManage.addData(x, low, close, high)

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

            self.stocks[p.symbol].updatePosition(p)

        closed = self.stocks.keys() - openset
        for s in closed:
            self.stocks[s].updatePosition(None)

    def updatePots(self):
        today = datetime.datetime.today().strftime(DATE_FMT)
        activities = self.api.get_activities('fill', date=today)

        for a in activities:
            stk = self.stocks[a.symbol]
            amnt = a.qty * a.price
            if a.side == 'buy':
                stk.addToPot(-amnt)
            elif a.side == 'sell':
                stk.addToPot(amnt)

    def position(self, stock: Stock):
        return self.api.get_position(stock.symbol)

    def run(self):
        global NEED_TO_STOP

        while not NEED_TO_STOP:
            # Inc trade day
            self.tradeDay += 1

            # wait for 15min before
            self.waitForMarketClose(15 * 60)

            # Update indicators with today's values
            self.updateIndicators()

            # Update positions and pots
            self.updatePositions()
            self.updatePots()

            # Calculate today's actions
            actions = self.getDailyActions()

            # Run actions
            for a in actions:
                self.runAction(a)

            # Wait for 1min after the market to close
            self.waitForMarketClose(-60)

            # Update positions and pits
            self.updatePositions()
            self.updatePots()

            # Send update email
            self.sendDailyUpdate(actions)

        print()
        print('Stopping System, Cancelling all existing order')
        self.api.cancel_all_orders()
        # Close all positions?
        # self.api.close_all_positions()
        print('Done')

    def getDailyActions(self) -> List[Action]:
        actions = []
        for sym, strat in self.strats.items():
            stk = self.stocks[sym]
            actions.append(strat.nextAction(self.tradeDay, stk))

        return actions

    def runAction(self, action: Action):
        if action.action == ActionEnum.Buy:
            self.submitBuy(action)
        elif action.action == ActionEnum.Sell:
            self.submitSell(action)
        elif action.action == ActionEnum.UpdateStop:
            self.submitUpdateStop(action)
        elif action.action == ActionEnum.Hold:
            # ILB
            pass

    def submitBuy(self, action: Action):

        try:
            order = self.api.submit_order(
                symbol=action.stock.symbol,
                qty=action.args['qty'],
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
            # TODO log buy action

        except KeyError as err:
            raise cmErrors.ActionError(f'Action missing argument: "{str(err)}", Action: {str(action)}')
        except alpaca.rest.APIError:
            # TODO err
            raise

    def submitSell(self, action: Action):
        # TOCHANGE allow partial sells?
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
            # TODO error
            raise

        # TODO log

    def submitUpdateStop(self, action: Action):
        try:
            order = self.api.replace_order(order_id=action.stock.order.id,
                                           stop_price=action.args['stopPrice'],
                                           limit_price=action.args['limitPrice'])
            # TODO log
            action.stock.order = order
        except KeyError as err:
            raise cmErrors.ActionError(f'Action missing argument: "{str(err)}", Action: {str(action)}')
        except alpaca.rest.APIError:
            # TODO err
            raise

    def sendDailyUpdate(self, actions: List[Action]):
        acts = {}
        for a in actions:
            acts[a.stock.symbol] = a

        header = f'Stock Algo Daily Update: {datetime.datetime.today()}\n\n'

        info = self.api.get_account()
        accountInfo = f'Account:\n' \
                      f'Buying Power: ${info.buying_power:.2f}\n\n'

        stkUpdates = ''
        for sym in sorted(self.strats.keys()):
            stkUpdates += f'Symbol: {sym}\n'
            stock = self.stocks[sym]
            stkUpdates += f'\tCurrent Buying Power Pot: ${stock.buyPower:.2f}'

            if stock.position is None:
                stkUpdates += f'\tStatus: Out Of Market\n'
            else:
                stkUpdates += f'\tStatus: In Market\n'
                stkUpdates += f'\t\tEntry Price: ${stock.position.avg_entry_price:.2f}\n'
                stkUpdates += f'\t\tQty: {stock.position.qty}\n'
                stkUpdates += f'\t\tCurrent Total Market Value: ${stock.position.market_value}\n'
                stkUpdates += f'P/L: ${stock.position.unrealized_pl:.2f}, {stock.position.unrealized_plpc:.2%}\n'

            stkUpdates += '\n'

            stkUpdates += f"\tToday's Action: {acts[sym].action.name}\n"
            for key, val in acts[sym].args:
                stkUpdates += f'\t\t{key}: {val}\n'

            stkUpdates += '\n'

        # TODO open orders?

        content = accountInfo + stkUpdates
        self.emailer.send(header, content)



    def clock(self) -> alpaca.rest.Clock:
        """Shorcut to get the API clock"""
        return self.api.get_clock()

    def waitForTS(self, ts):
        """Utility to wait until timestamp"""

        # TODO use log

        while True:
            clock = self.clock()
            diff = ts - toTS(clock.timestamp)
            if diff <= 0:
                return

            if diff > 6:
                print(f'Waiting {diff / 60:.2f}min')
                timeToSleep = diff - 5
                sleep(timeToSleep)
            else:
                sleep(2)

    def waitForMarketClose(self, delta=0):
        """Waits till delta secs before market close"""
        clock = self.clock()

        if clock.is_open:
            self.waitForTS(toTS(clock.close_time) - delta)

        print('Market Closed')

    def waitForMarketOpen(self, delta=0):
        """Waits till delta secs before market open"""
        clock = self.clock()
        if not clock.is_open:
            self.waitForTS(toTS(clock.open_time) - delta)

        print('Market Open')


PAPER_ENDPOINT = 'https://paper-api.alpaca.markets'
LIVE_ENDPOINT = 'https://api.alpaca.markets'


def main():
    parser = ArgumentParser()

    parser.add_argument('-s', '--strat', required=True)
    parser.add_argument('-stx', '--stocks', required=True)
    parser.add_argument('--liveRun', action='store_true')

    args = parser.parse_args()

    config = dotenv_values('ignore/.env')

    if args.liveRun:
        x = input('Are you sure you want to run using the LIVE ACCOUNT? (YES/NO):')
        if x != 'YES':
            print('System Exiting')
            return
        else:
            print('Initializing Live Account')
            api_key = config['LIVE_API_KEY_ID']
            api_secret = config['LIVE_SECRET']
            endpoint = LIVE_ENDPOINT
    else:
        print('Initializing Paper Account')
        api_key = config['PAPER_API_KEY_ID']
        api_secret = config['PAPER_SECRET']
        endpoint = PAPER_ENDPOINT

    print('Loading Strategy')
    stratVars = loadStratFile(args.strat)

    print('Loading Stocks')
    stocks = loadStockFile(args.stocks)

    api = alpaca.REST(api_key, api_secret, URL(endpoint), 'v2')

    strats = {}
    for sym in stocks:
        strats[sym] = HardStrategy(sym, stratVars)

    emailer = CMEmailer(config)

    trader = Trader(strats, api, emailer)
    trader.run()


def exitHandler(signum, x):
    global NEED_TO_STOP
    NEED_TO_STOP = True
    if signum != signal.SIGINT:
        print('Critical Err, signum:', signum)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exitHandler)

    main()
