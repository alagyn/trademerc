import time
from datetime import datetime
import backtrader as bt
from argparse import ArgumentParser
import os
import configparser
from strategies.master_strategy import MasterStrategy
import yfinance as yf

# TODO remove/update
"""
# Record information to excel file
def record():
    filename = 'record.csv'
    file_exists = os.path.isfile(filename)
    # updates the history file to write into it, if "a" value was a "w" the function would write over the existing data
    with open(filename, 'a', newline="") as backtest_record:  
        fieldnames = ["Stock", "Value", "Profit($)", "Percent Gained(%)", "Total Trades", "Win %", "SQN"]
        writer = csv.DictWriter(backtest_record, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header
        writer.writerow({'Stock': stock,
                         'Value': ending_value,
                         'Profit($)': str(round(ending_value - starting_value, 2)),
                         'Percent Gained(%)': str(round(((ending_value - starting_value) / starting_value), 2)),
                         'Total Trades': tt,
                         'Win %': win,
                         'SQN': sqn
                         })
"""


# Analyzes the efficiency of trade
def tradeAnalysis(strat):
    analyzer = strat.analyzers.ta.get_analysis()
    tt = analyzer.won.total + analyzer.lost.total
    win = analyzer.won.total / (analyzer.won.total + analyzer.lost.total)

    print(f'Total Trades: {analyzer.won.total + analyzer.lost.total:.2f}')
    # print('Win percentage: %.2f' % (analyzer.won.total / (analyzer.won.total + analyzer.lost.total) * 100) + '%')
    # print('Won: %s' % analyzer.won.total)
    # print('Lost: %s' % analyzer.lost.total)
    # print('Opened: %s' % analyzer.total.open)
    # print('Closed: %s' % analyzer.total.closed)
    # print('Win Streak: %s' % analyzer.streak.won.longest)
    # print('Lose Streak: %s' % analyzer.streak.lost.longest)
    # print('P&L: %.2f' % analyzer.pnl.net.total)
    print(f'Win Percent: {win:.2%}')


# System Quality Number. Goal is above 3
def sqn(strat):
    analyzer = strat.analyzers.sqn.get_analysis()
    return analyzer.sqn


def main():
    parser = ArgumentParser()
    parser.add_argument(
        '--stocks', '-stx',
        required=True,
        type=str
    )

    parser.add_argument(
        '--strategy', '-str',
        required=True,
        type=str
    )

    args = parser.parse_args()

    start_date = datetime(2018, 1, 1)
    end_date = datetime.today()

    stocks = []

    if os.path.exists(args.stocks):
        with open(args.stocks, mode='r') as f:
            lines = [x.strip() for x in f.readlines()]
            for x in lines:
                if not x.startswith('#'):
                    stocks.append(x)
    else:
        print('Invalid Stock list file')


    config = configparser.ConfigParser()
    config.read(args.strategy)

    cerebro = bt.Cerebro()  # Create a cerebro entity

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")  # Adds trade analyzer
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")  # Adds SQN analyzer

    cerebro.addstrategy(MasterStrategy, config)

    cerebro.addsizer(bt.sizers.PercentSizer, percents=100)  # Sets the amount willing to risk per trade

    fmt = '%Y-%m-%d'
    sd = start_date.strftime(fmt)
    ed = end_date.strftime(fmt)

    for stock in stocks:
        data = bt.feeds.PandasData(dataname=yf.download(stock, sd, ed, auto_adjust=True))
        cerebro.adddata(data)
        print(f'Stock: {stock}')

    cerebro.broker.setcash(10000)  # Sets initial portfolio amount

    startingValue = cerebro.broker.getvalue()

    t0 = time.time()
    results = cerebro.run()
    duration = time.time() - t0

    endingValue = cerebro.broker.getvalue()
    strat = results[0]

    print("")
    print(f'Run Time: {duration:.2f}s')
    print(f'Stock: {stock}')
    print(f'Ending Value: {endingValue:.2f}')
    print(f'Profit: {endingValue - startingValue:.2f}')
    percentGain = (endingValue - startingValue) / startingValue
    print(f'Percent Gained: {percentGain:.2%}%')
    tradeAnalysis(strat)
    print(f'SQN: {sqn(strat):.2f}')

    cerebro.plot()
    # TODO remove?
    # record()


if __name__ == '__main__':
    main()
