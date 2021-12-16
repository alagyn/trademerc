import datetime

from alpaca_trade_api.common import URL
from dotenv import dotenv_values
from argparse import ArgumentParser
from backtester import loadStratFile, loadStockFile
import alpaca_trade_api as tradeapi
import threading
from time import sleep
import signal

NEED_TO_STOP = False


def toTS(time):
    return time.replace(tzinfo=datetime.timezone.utc).timestamp()


class Stock:
    def __init__(self, symbol: str):
        self.symbol: str = symbol
        self.confidence = 0
        self.status = ''
        self.stopID = ''
        self.buyDate = ''

        self.indct = {}


class Trader:
    def __init__(self, strat, stx, api: tradeapi.REST):
        self.api = api
        info = self.api.get_account()
        self.equity = float(info.equity)
        print(self.equity)

        self.confidences = {}

        for x in stx:
            self.confidences[x] = Stock(x)

        # TODO init indicators with old data?
        # Initialize confidences too

    def position(self, stock: Stock):
        return self.api.get_position(stock.symbol)

    def run(self):
        global NEED_TO_STOP

        # First cancel any existing orders?
        self.api.cancel_all_orders()

        while not NEED_TO_STOP:
            is_open, curTime, openTime = self.clock()
            if not is_open:
                self.updConf()

                self.waitForMarketOpen()

        print()
        print('Stopping System, Cancelling all existing order')
        self.api.cancel_all_orders()
        print('Done')

    def updConf(self):
        # TODO
        pass

    def clock(self):
        return self.api.get_clock()

    def waitForTS(self, ts):
        while True:
            clock = self.clock()
            diff = ts - toTS(clock.timestamp)
            if diff < 0:
                return

            if diff > 6:
                print(f'Waiting {diff / 60:.2f}min')
                timeToSleep = diff - 5
                sleep(timeToSleep)
            else:
                sleep(2)

    def waitForMarketClose(self):
        clock = self.clock()
        if clock.is_open:
            self.waitForTS(toTS(clock.close_time))

        print('Market Closed')

    def waitForMarketOpen(self):
        clock = self.clock()
        if not clock.is_open:
            self.waitForTS(toTS(clock.open_time))

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

    api = tradeapi.REST(api_key, api_secret, URL(endpoint), 'v2')

    trader = Trader(stratVars, stocks, api)
    trader.run()


def exitHandler(signum, x):
    global NEED_TO_STOP
    NEED_TO_STOP = True
    if signum != signal.SIGINT:
        print('Critical Err, signum:', signum)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exitHandler)

    main()
