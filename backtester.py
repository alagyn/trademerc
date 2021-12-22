import time
from datetime import datetime
import backtrader as bt
from argparse import ArgumentParser
from bt_strategies.master_strategy import MasterStrategy
from cmErrors import *
import yfinance as yf
import json
from consts import STRAT_FORMAT, DATE_FMT
from typing import List


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


def loadStockFile(file):
    stocks = []
    with open(file, mode='r') as f:
        lines = [x.strip() for x in f.readlines()]
        for x in lines:
            if not x.startswith('#'):
                stocks.append(x)

    return stocks


def loadStratFile(file):
    with open(file, mode='r') as f:
        strat = json.load(f)
        verifyStrat(strat)
        return strat


def recursVerify(fmt, strat, path):
    for key, val in fmt.items():
        curPath = path + '->' + key
        try:
            stratVal = strat[key]
        except KeyError:
            raise JSONStrategyMissingVal(curPath)

        if not isinstance(stratVal, type(val)):
            if not (isinstance(val, float) and isinstance(stratVal, int)):
                raise JSONStrategyInvalidType(curPath, type(val), type(stratVal))

        if isinstance(val, dict):
            recursVerify(val, stratVal, curPath)


def verifyStrat(strat):
    with open(STRAT_FORMAT, mode='r') as f:
        fmt = json.load(f)

    # print(fmt)
    recursVerify(fmt, strat, "root")


def backtest(stocks: List[str], strat, start_date: str, end_date: str, outputFile, startingVal=10000):

    for stock in stocks:
        cerebro = bt.Cerebro()  # Create a cerebro entity

        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")  # Adds trade analyzer
        cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")  # Adds SQN analyzer

        cerebro.addstrategy(MasterStrategy, strat['variables'])

        cerebro.addsizer(bt.sizers.PercentSizer, percents=100)  # Sets the amount willing to risk per trade

        data = bt.feeds.PandasData(dataname=yf.download(stock, start_date, end_date, auto_adjust=True))
        cerebro.adddata(data)
        print(f'Stock: {stock}')

        cerebro.broker.setcash(startingVal)  # Sets initial portfolio amount

        startingValue = cerebro.broker.getvalue()

        t0 = time.time()
        results = cerebro.run()
        duration = time.time() - t0

        endingValue = cerebro.broker.getvalue()
        results = results[0]

        print("")
        print(f'Run Time: {duration:.2f}s')
        # print(f'Stock: {stock}')
        print(f'Ending Value: ${endingValue:.2f}')

        profit = endingValue - startingValue
        print(f'Profit: ${profit:.2f}')
        percentGain = (endingValue - startingValue) / startingValue
        print(f'Percent Gained: {percentGain:.2%}')
        tradeAnalysis(results)
        sqnVal = sqn(results)
        print(f'SQN: {sqnVal:.2f}')

        stats = {
            'Strat': strat['name'],
            'Stock': stock,
            'StartValue': startingVal,
            'EndValue': round(endingValue, 2),
            'Profit': round(profit, 2),
            'PercentGain': round(percentGain, 4),
            'SQN': round(sqnVal, 4)
        }

        with open(outputFile, mode='a') as f:
            json.dump(stats, f)
            f.write('\n')

    # print('Plotting')
    # cerebro.plot()
    # record()
    # print('Done')


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


def main():
    parser = ArgumentParser()
    parser.add_argument(
        '--stock', '-stk',
        required=True,
        type=str
    )

    parser.add_argument(
        '--strategy', '-str',
        required=True,
        type=str
    )

    args = parser.parse_args()
    strat = loadStratFile(args.strategy)

    start_date = datetime(2018, 1, 1).strftime(DATE_FMT)
    end_date = datetime.today().strftime(DATE_FMT)

    try:
        backtest(args.stock, strat, start_date, end_date)
    except StrategyError as err:
        print(err)


if __name__ == '__main__':
    main()
