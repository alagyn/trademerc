from alpaca_trade_api.common import URL
from dotenv import dotenv_values
from argparse import ArgumentParser
from backtester import loadStratFile, loadStockFile
import alpaca_trade_api as tradeapi
from asyncio import sleep

class Trader:
    def __init__(self, strat, stx, api: tradeapi.REST):
        self.api = api
        info = self.api.get_account()
        self.equity = float(info.equity)


    async def run(self):
        # First cancel any existing orders?
        pass

    async def waitForMarketOpen(self):
        if not self.api.get_clock().is_open:
            pass


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


if __name__ == '__main__':
    main()
