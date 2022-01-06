import time
from datetime import datetime, timedelta
import math
import numpy as np

from alpaca_trade_api.rest import REST

import cmErrors
from indicators.indicator import IndicatorManager
from strategies.strategy import Strategy
from objects.stock import Stock
from objects.action import ActionEnum
from utils.api_utils import getBars, calcSetupStartDate
from consts import DATE_FMT

from typing import Dict
import json


class Stats:
    def __init__(self, startingValue):
        self.value = startingValue
        self.valueBeforeBuy = 0
        self.lossList = []
        self.winList = []
        self.numTrades = 0

    def updateWL(self):
        delta = self.value - self.valueBeforeBuy

        if self.value < self.valueBeforeBuy:
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


def setupBacktest(api: REST, symbols, startDate: datetime, endDate: datetime):
    iManage = IndicatorManager()
    setupTime = iManage.getSetupTime()

    setupStart = calcSetupStartDate(startDate - timedelta(1), setupTime)

    startstr = setupStart.strftime(DATE_FMT)
    endstr = endDate.strftime(DATE_FMT)

    # load bars and setup indicators
    length = 0
    allBars = {}
    for sym in symbols:
        b = getBars(api, sym, startstr, endstr)
        allBars[sym] = b
        lo = b['low']
        c = b['close']
        hi = b['high']
        length = len(hi)
        for i in range(setupTime):
            iManage.addData(sym, lo[i], c[i], hi[i])

    return allBars, setupTime, length


def checkStop(stop):
    if stop < 0:
        raise cmErrors.BacktestError(f'Stop Price Below zero: ${stop:.2f}')


def backtest(api: REST, stratName: str, strats: Dict[str, Strategy], startDate: datetime, endDate: datetime,
             startingVal=10000,
             outputFile: str = 'stats.json'):
    allBars, setupTime, totalLen = setupBacktest(api, strats.keys(), startDate, endDate)
    iManage = IndicatorManager()


    totalCash = startingVal
    stats = {}
    stops = {}
    qty = {}
    stocks = {}

    for sym in strats.keys():
        stocks[sym] = Stock(sym)
        qty[sym] = 0
        stats[sym] = Stats(0)

    try:
        for i in range(setupTime, totalLen):
            day = i - setupTime
            print(f"Trade Day: {day}")

            perStockBP = 0
            for sym in strats.keys():
                if sym in stops and stops[sym] > allBars[sym]['low'][i]:
                    print(f'\t{sym}: Stop Activated')

                    newCash = qty[sym] * stops[sym]
                    totalCash += newCash

                    qty[sym] = 0
                    stops.pop(sym)
                    stocks[sym].position = None

                    stats[sym].value = newCash
                    stats[sym].updateWL()

                if stocks[sym].position is None:
                    perStockBP += 1

            perStockBP = 0 if perStockBP == 0 else round(totalCash / perStockBP, 2)

            for sym, strat in strats.items():
                lo = allBars[sym]['low'][i]
                close = allBars[sym]['close'][i]
                hi = allBars[sym]['high'][i]

                iManage.addData(sym, lo, close, hi)

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

                    # Set initial value
                    stat.valueBeforeBuy = trueCost

                    totalCash -= trueCost

                    stat.numTrades += 1

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
                    stat.value = soldValue
                    stat.updateWL()

                elif act.action == ActionEnum.UpdateStop:
                    checkStop(act.args['stopPrice'])
                    stops[sym] = act.args['stopPrice']
                else:
                    # Hold, ILB
                    pass

                print("\t", act)

                if totalCash < 0:
                    raise cmErrors.BacktestError('Negative Value, Strategy Failure?')
        # END Main for loop

        # clear out any remaining positions
        for sym, q in qty.items():
            if q > 0:
                newCash = q * allBars[sym]['close'][-1]
                stats[sym].value = newCash
                stats[sym].updateWL()

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
    print(f'Wins: {wins}, Losses: {losses}, W/L: {wlRatio:.2f}')
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
