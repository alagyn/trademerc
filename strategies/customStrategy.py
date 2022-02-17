from typing import List

import cmErrors
from checks import *
from indicators import *
from objects.stock import *
from .strategy import *


class CheckList:
    def __init__(self, checks: List[Check] = None):
        self._checks: List[Check] = [] if checks is None else checks

    def addCheck(self, c: Check):
        self._checks.append(c)

    def check(self) -> bool:
        value = True

        for c in self._checks:
            value = value and c.check()

        return value


class StopCalculation:
    def __init__(self, value, scale: float, limitScale: float):
        self._valF = value
        self._scale = scale
        self._lscale = limitScale

    def __call__(self):
        stop = self._valF() * self._scale
        return stop, stop * self._lscale


class CustomStrategy(Strategy):
    def dryRun(self) -> None:
        # TODO
        pass

    def __init__(self, name: str, symbol: str, indicators: List[Indicator], enterCond: Check, exitCond: Check,
                 stopCalc: StopCalculation = None, stopUpdatePeriod=0):

        super().__init__(symbol, name, IndicatorManager(indicators))

        self.enterCond = enterCond
        self.exitCond = exitCond
        self.stopCalc = stopCalc
        self.stopPeriod = stopUpdatePeriod
        self.nextStop = 0

    def nextAction(self, day: int, stock: Stock) -> Action:
        pos = stock.status()

        # In Market
        if pos == StockStatus.InMarket:
            if self.exitCond.check():
                return stock.sell()

            if self.stopCalc is not None and day >= self.nextStop:
                self.nextStop = day + self.stopPeriod
                stop, limit = self.stopCalc()
                return stock.updateStop(stop, limit)

        # Out Market
        elif pos == StockStatus.OutMarket:
            if self.enterCond.check():
                self.nextStop = day + self.stopPeriod
                if self.stopCalc is not None:
                    stop, limit = self.stopCalc()
                    return stock.buyAndStop(stop, limit)
                else:
                    return stock.buy()

        return Action(stock, ActionEnum.Hold)


def makeCustomStrategy(stratvars, symbol: str) -> CustomStrategy:
    # TODO json error catching
    # TODO warn if an indicator is not used

    all_inds: List[Indicator] = []

    for i in stratvars['indicators']:
        newind = INDICATORS[i['class']](**i['args'])
        all_inds.append(newind)

    all_checks = []

    for c_idx, c in enumerate(stratvars['checks']):
        valFuncs = []
        for i in c['indicators']:
            idx = i['idx']
            key = i['key']
            valFuncs.append(all_inds[idx][key])

        checks = []

        for i in c['checks']:
            if i >= c_idx:
                raise cmErrors.StrategyError('Invalid Check Idx')
            checks.append(all_checks[i])

        newcheck = CHECKS[c['class']].factory(valFuncs, checks, c['args'])
        all_checks.append(newcheck)

    enterCondIdx = stratvars['enterCond']
    exitCondIdx = stratvars['exitCond']

    stopCalcIdx = stratvars['stopCalc']['indicator']
    stopCalcKey = stratvars['stopCalc']['key']

    stopCalcVal = all_inds[stopCalcIdx][stopCalcKey]
    stopScale = stratvars['stopCalc']['scale']
    stopLimitScale = stratvars['stopCalc']['limitScale']

    stopCalc = StopCalculation(stopCalcVal, stopScale, stopLimitScale)

    return CustomStrategy(
        name=stratvars['name'],
        symbol=symbol,
        indicators=all_inds,
        enterCond=all_checks[enterCondIdx],
        exitCond=all_checks[exitCondIdx],
        stopCalc=stopCalc,
        stopUpdatePeriod=stratvars['daysToUpdateStop']
    )
