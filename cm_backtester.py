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


def calcSQN(stats: Stats) -> float:
    """
    Calculates the System Quality Number
    Should be reliable if stats.numTrades >= 30

    :param stats: The trade statistics
    :return: The SQN
    """
    # get list of every trade
    totalProfits = stats.winList.copy()
    totalProfits.extend(stats.lossList)
    tp = np.array(totalProfits)

    a = math.sqrt(stats.numTrades)
    # avg profit
    b = np.average(tp)
    # profit std
    c = np.std(tp)

    return a * b / c


def backtest(api: REST, strats: Dict[str, Strategy], startDate: datetime, endDate: datetime, startingVal=10000,
             outputFile: str = 'stats.json'):
    iManage = IndicatorManager()
    setupTime = iManage.getSetupTime()

    setupStart = calcSetupStartDate(startDate - timedelta(1), setupTime)

    startstr = setupStart.strftime(DATE_FMT)
    endstr = endDate.strftime(DATE_FMT)

    allBars = {}
    for sym in strats.keys():
        b = getBars(api, sym, startstr, endstr)
        allBars[sym] = b
        lo = b['low']
        c = b['close']
        hi = b['high']
        for i in range(setupTime):
            iManage.addData(sym, lo[i], c[i], hi[i])

    for sym, strat in strats.items():
        stock = Stock(sym)

        bars = allBars[sym]

        lows = bars['low']
        closes = bars['close']
        highs = bars['high']

        currentStop = None
        stats = Stats(startingVal)

        ownedQty = 0

        try:

            def checkStop(stop):
                if stop < 0:
                    raise cmErrors.BacktestError(f'Stop Price Below zero: ${stop:.2f}')


            for i in range(setupTime, len(bars)):
                day = i - setupTime

                lo = lows[day]
                close = closes[day]
                hi = highs[day]

                iManage.addData(sym, lo, close, hi)

                if currentStop is not None and lo <= currentStop:
                    print('Stop Activated')

                    stats.value += ownedQty * currentStop
                    ownedQty = 0
                    stats.updateWL()

                    stock.position = None
                    currentStop = None

                act = strat.nextAction(day, stock)

                print(f'Day: {day}, [{lo:.2f}, {close:.2f}, {hi:.2f}]')
                print(f'\t{act}')


                if act.action == ActionEnum.Buy:
                    # Set position to non-None
                    stock.position = "InMarket"
                    # Set new stop
                    checkStop(act.args['stopPrice'])
                    currentStop = act.args['stopPrice']
                    # Set initial value
                    stats.valueBeforeBuy = stats.value
                    # Calc max whole stocks we can buy
                    stocksToBuy = int(stats.value / close)
                    # update qty
                    ownedQty = stocksToBuy
                    # Update value
                    trueCost = stocksToBuy * close
                    stats.value -= trueCost

                    stats.numTrades += 1

                elif act.action == ActionEnum.Sell:
                    # Clear position
                    stock.position = None
                    # Clear stop
                    currentStop = None
                    # Update value
                    soldValue = ownedQty * close
                    stats.value += soldValue
                    ownedQty = 0
                    # Update win/loss
                    stats.updateWL()

                elif act.action == ActionEnum.UpdateStop:
                    checkStop(act.args['stopPrice'])
                    currentStop = act.args['stopPrice']
                else:
                    # Hold, ILB
                    pass

                if stats.value < 0:
                    print('Negative Value, Strategy Failure?')
                    break

            if ownedQty > 0:
                stats.value += ownedQty * closes[-1]
                stats.updateWL()
        except cmErrors.BacktestError as err:
            print(f'BACKTEST ERROR: {err}')

        wins = len(stats.winList)
        losses = len(stats.lossList)
        winTotal = sum(stats.winList)
        lossTotal = sum(stats.lossList)

        profit = stats.value - startingVal
        percentGain = profit / startingVal
        sqnVal = calcSQN(stats)

        print(f'Start Value: ${startingVal:.2f}, End Value: ${stats.value:.2f}')
        print(f'Profit: {profit:.2f}, Percent Gain: {percentGain:.2%}')
        print(f'Wins: {wins}, Losses: {losses}, W/L: {wins / losses:.2f}')
        print(f'Win %: {wins / (wins + losses):.2%}')
        print(f'Avg Gain: ${winTotal / wins:.2f}')
        print(f'Avg Loss: ${lossTotal / losses:.2f}')
        print(f'SQN: {sqnVal:.3f}')

        statDict = {
            'Strat': strat.getName(),
            'Stock': stock.symbol,
            'StartValue': startingVal,
            'EndValue': round(stats.value, 2),
            'Profit': round(profit, 2),
            'PercentGain': round(percentGain, 4),
            'SQN': round(sqnVal, 4)
        }

        with open(outputFile, mode='a') as f:
            json.dump(statDict, f)
            f.write('\n')
