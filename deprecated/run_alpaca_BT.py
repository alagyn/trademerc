from dotenv import dotenv_values
from argparse import ArgumentParser
import alpaca_backtrader_api as alpaca
from bt_strategies.master_strategy import MasterStrategy
from bt_backtester import loadStratFile, loadStockFile
import backtrader as bt
import pandas as pd
from datetime import datetime


def main():
    parser = ArgumentParser()

    parser.add_argument('-s', '--strat', required=True)
    parser.add_argument('-stx', '--stocks', required=True)
    parser.add_argument('--backtest', action='store_true')
    parser.add_argument('--liveRun', action='store_true')

    args = parser.parse_args()

    config = dotenv_values('ignore/.env')

    if args.liveRun:
        x = input('Are you sure you want to run using the LIVE ACCOUNT? (YES/NO):')
        if x != 'YES':
            print('System Exiting')
            exit()
        else:
            api_key = config['LIVE_API_KEY_ID']
            api_secret = config['LIVE_SECRET']
            raise NotImplementedError()
    else:
        api_key = config['PAPER_API_KEY_ID']
        api_secret = config['PAPER_SECRET']

    print(f'Init Alpaca Store, Paper: {not args.liveRun}')
    store = alpaca.AlpacaStore(
        key_id=api_key,
        secret_key=api_secret,
        paper=not args.liveRun
    )

    print('Loading Strategy')
    stratVars = loadStratFile(args.strat)

    print('Initializing Cerebro')
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MasterStrategy, stratVars['variables'])

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

    # Sets the amount willing to risk per trade
    cerebro.addsizer(bt.sizers.PercentSizer, percents=100)

    if args.liveRun:
        print('Initializing Live Trading')
        broker = store.getbroker()
        cerebro.setbroker(broker)

    print('Loading Stocks')
    stocks = loadStockFile(args.stocks)

    for stock in stocks:
        if args.backtest:
            d = store.getdata(
                dataname=stock,
                timeframe=bt.TimeFrame.Days,
                fromdate=datetime(2018, 1, 1),
                todate=datetime(2021, 1, 1),
                historical=True
            )
        else:
            d = store.getdata(
                dataname=stock,
                timeframe=bt.TimeFrame.Days
            )

        cerebro.adddata(d)

    print(f'Running Cerebro, Starting Value: {cerebro.broker.getvalue()}')
    try:
        cerebro.run()
    except KeyboardInterrupt:
        pass
    print(f'Final Value: {cerebro.broker.getvalue()}')
    cerebro.plot(style='candlestick', barup='green', bardown='red')


if __name__ == '__main__':
    main()
