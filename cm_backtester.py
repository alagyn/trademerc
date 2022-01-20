from datetime import datetime, timedelta
import math
import numpy as np
import matplotlib as mpl
import matplotlib.dates as mplDates
from matplotlib.dates import ConciseDateFormatter
from matplotlib.figure import Figure, Axes

import yfinance as yf

import cmErrors
from strategies.strategy import Strategy
from objects.stock import Stock
from objects.action import ActionEnum
from utils.api_utils import getBars, calcSetupStartDate
from consts import DATE_FMT

from typing import Dict
import json

# TODO remove
from strategies.hardStrategy import HardStrategy


from utils.file_utils import loadStratFile

CLOSE = 'Close'
LOW = 'Low'
HIGH = 'High'


class Stats:
    def __init__(self):
        self.startingVal = 0
        self.lossList = []
        self.winList = []

        self.buyDays = []
        self.buyPrices = []

        self.sellDays = []
        self.sellPrices = []
        self.sellDeltas = []

    def addBuy(self, day, value, unitCost):
        self.startingVal = value
        self.buyDays.append(day)
        self.buyPrices.append(unitCost)

    def addSell(self, day, value, unitSell):
        delta = value - self.startingVal
        self.sellDays.append(day)
        self.sellPrices.append(unitSell)
        self.sellDeltas.append(delta)

        if delta < 0:
            self.lossList.append(delta)
        else:
            self.winList.append(delta)


def calcSQN(tradeList) -> float:
    """
    Calculates the System Quality Number
    Should be reliable if stats.numTrades >= 30
    """

    arr = np.array(tradeList)

    a = math.sqrt(len(tradeList))
    # avg profit
    b = np.average(arr)
    # profit std
    c = np.std(arr)

    return a * b / c


def setupBacktest(strats: Dict[str, Strategy], startDate: datetime, endDate: datetime):
    setupTime = max([x.getSetupTime() for x in strats.values()])

    setupStart = calcSetupStartDate(startDate - timedelta(1), setupTime)

    startstr = setupStart.strftime(DATE_FMT)

    endstr = endDate.strftime(DATE_FMT)

    # load bars and setup indicators
    length = 0
    allBars = {}
    for sym, strat in strats.items():
        b = yf.download(sym, startstr, endstr)
        allBars[sym] = b
        lo = b['Low']
        c = b['Close']
        hi = b['High']
        length = len(hi)
        for i in range(setupTime):
            strat.addData(lo[i], c[i], hi[i])
            try:
                strat.dryRun()
            except cmErrors.NotSetupError:
                pass

    return allBars, setupTime, length


def checkStop(stop):
    if stop < 0:
        raise cmErrors.BacktestError(f'Stop Price Below zero: ${stop:.2f}')


def backtest(stratName: str, strats: Dict[str, Strategy],
             masterFigure: Figure, symFigs: Dict[str, Figure],
             startDate: datetime, endDate: datetime,
             startingVal=10000, outputFile: str = 'stats.json',
             ):
    allBars, setupTime, totalLen = setupBacktest(strats, startDate, endDate)

    totalCash = startingVal
    stats = {}
    stops = {}
    qty = {}
    stocks = {}

    runtime = totalLen - setupTime


    datekey = list(strats.keys())[0]
    dates = []

    portfolio_cash = np.array([0.0] * runtime)
    portfolio_value = np.array([0.0] * runtime)

    # need to track:
    #   total equity per day
    #   trades
    #   indicators can register?

    for sym in strats.keys():
        stocks[sym] = Stock(sym)
        qty[sym] = 0
        stats[sym] = Stats()

    try:
        for i in range(setupTime, totalLen):
            day = i - setupTime
            print(f"Trade Day: {day}")

            dates.append(allBars[datekey].index[i])

            # check for activated stops and calculates the number of stocks that are OOM
            perStockBP = 0
            for sym in strats.keys():
                if sym in stops and stops[sym] > allBars[sym][LOW][i]:
                    print(f'\t{sym}: Stop Activated')

                    newCash = qty[sym] * stops[sym]
                    totalCash += newCash

                    stats[sym].addSell(day, newCash, stops[sym])

                    qty[sym] = 0
                    stops.pop(sym)
                    stocks[sym].position = None

                if stocks[sym].position is None:
                    perStockBP += 1

            perStockBP = 0 if perStockBP == 0 else round(totalCash / perStockBP, 2)

            inMarketEquity = 0

            for sym, strat in strats.items():
                lo = allBars[sym][LOW][i]
                close = allBars[sym][CLOSE][i]
                hi = allBars[sym][HIGH][i]

                strat.addData(lo, close, hi)

                stock = stocks[sym]

                stat = stats[sym]

                act = strat.nextAction(day, stock)

                if act.action == ActionEnum.Buy:
                    # Set position to non-None
                    stock.position = "InMarket"
                    # Set new stop
                    checkStop(act.args['stopPrice'])
                    stops[sym] = act.args['stopPrice']
                    # Calc max whole stocks we can buy
                    stocksToBuy = math.floor(perStockBP / close)
                    # update qty
                    qty[sym] = stocksToBuy
                    # Update value
                    trueCost = stocksToBuy * close

                    stat.addBuy(day, trueCost, close)

                    totalCash -= trueCost


                elif act.action == ActionEnum.Sell:
                    # Clear position
                    stock.position = None
                    # Clear stop
                    stops.pop(sym)
                    # Update value
                    soldValue = qty[sym] * close
                    totalCash += soldValue

                    qty[sym] = 0
                    # Update win/loss
                    stat.addSell(day, soldValue, close)

                elif act.action == ActionEnum.UpdateStop:
                    checkStop(act.args['stopPrice'])
                    stops[sym] = act.args['stopPrice']
                else:
                    # Hold, ILB
                    pass

                print(f"\t{act}")

                if qty[sym] > 0:
                    inMarketEquity += qty[sym] * close

                if totalCash < 0:
                    raise cmErrors.BacktestError('Negative Value, Strategy Failure?')
            # END symbol action loop

            # update graph logs
            portfolio_cash[day] = round(totalCash, 2)
            portfolio_value[day] = round(inMarketEquity, 2)
            print(f"\tTotal Value: ${totalCash + inMarketEquity: .2f}")

        # END Main for loop

        # clear out any remaining positions
        for sym, q in qty.items():
            if q > 0:
                sellPrice = allBars[sym][CLOSE][-1]
                newCash = q * sellPrice
                stats[sym].addSell(runtime, newCash, sellPrice)
                totalCash += newCash

    except cmErrors.BacktestError as err:
        print(f'BACKTEST ERROR: {err}')
        return

    wins = 0
    losses = 0
    winTotal = 0
    lossTotal = 0

    tradeList = []

    for sym, stat in stats.items():
        wins += len(stat.winList)
        losses += len(stat.lossList)
        winTotal += sum(stat.winList)
        lossTotal += sum(stat.lossList)

        tradeList.extend(stat.winList)
        tradeList.extend(stat.lossList)

    numTrades = len(tradeList)
    profit = totalCash - startingVal
    percentGain = profit / startingVal

    sqnVal = 0 if numTrades <= 1 else calcSQN(tradeList)
    wlRatio = 1 if losses == 0 else wins / losses
    avgGain = 0 if wins == 0 else winTotal / wins
    avgLoss = 0 if losses == 0 else lossTotal / losses

    winPercent = 0 if numTrades == 0 else wins / (wins + losses)

    print(f'Start Value: ${startingVal:.2f}, End Value: ${totalCash:.2f}')
    print(f'Profit: {profit:.2f}, Percent Gain: {percentGain:.2%}')
    print(f'Trades: {numTrades}, Wins: {wins}, Losses: {losses}, W/L: {wlRatio:.2f}')
    print(f'Win %: {winPercent:.2%}')
    print(f'Avg Gain: ${avgGain:.2f}')
    print(f'Avg Loss: ${avgLoss:.2f}')
    print(f'SQN: {sqnVal:.3f}')

    statDict = {
        'Strat': stratName,
        'StartValue': startingVal,
        'EndValue': round(totalCash, 2),
        'Profit': round(profit, 2),
        'PercentGain': round(percentGain, 4),
        'SQN': round(sqnVal, 4)
    }

    with open(outputFile, mode='a') as f:
        json.dump(statDict, f)
        f.write('\n')

    print("Plotting")
    if masterFigure is not None:
        masterAxes = masterFigure.add_subplot()
        r = range(len(portfolio_cash))

        portfolio_total = np.add(portfolio_cash, portfolio_value)

        masterAxes.bar(dates, portfolio_cash, label='Cash', color='C1', width=1, align='edge')
        masterAxes.plot(dates, portfolio_total, label='Value')

        locator = mplDates.AutoDateLocator(minticks=5, maxticks=10)
        dateformat = ConciseDateFormatter(locator)
        masterAxes.xaxis.set_major_locator(locator)
        masterAxes.xaxis.set_major_formatter(dateformat)

        masterAxes.grid(True)
        masterAxes.legend()

        for sym in strats.keys():
            axes = symFigs[sym].subplot_mosaic([['top'],
                                                ['bot'],
                                                ['bot']], sharex=True)

            topPlot = axes['top']
            botPlot = axes['bot']

            closes = allBars[sym][CLOSE][setupTime:]

            botPlot.plot(dates, closes, label=sym, color=(0, 0, 0))

            stat = stats[sym]

            buyDays = [dates[x] for x in stat.buyDays]
            sellDays = [dates[x] for x in stat.sellDays]

            botPlot.scatter(buyDays, stat.buyPrices, marker='^', color=(0.1, 0.75, 0.1), label='Buys', zorder=2.5)
            botPlot.scatter(sellDays, stat.sellPrices, marker='v', color=(1, 0.1, 0.1), label='Sells', zorder=2.5)

            botPlot.xaxis.set_major_locator(locator)
            botPlot.xaxis.set_major_formatter(dateformat)

            botPlot.legend()
            botPlot.grid(True)

            color = ['g' if x > 0 else 'r' for x in stat.sellDeltas]

            topPlot.scatter(sellDays, stat.sellDeltas, color=color, label='Profit/Loss')
            topPlot.set_yticks([0])
            topPlot.grid(True)

            topPlot.legend()


def _main():
    parser = ArgumentParser()

    parser.add_argument(
        '--strategy', '-str',
        required=True,
        type=str
    )

    args = parser.parse_args()
    strat = loadStratFile(args.strategy)

    start_date = datetime(2018, 1, 1)
    end_date = datetime.today()

    backtest('TEST', strats={'QQQ': HardStrategy('QQQ', strat)}, masterAxes=None, symAxes=None,
             startDate=start_date, endDate=end_date)


if __name__ == '__main__':
    from argparse import ArgumentParser

    _main()
