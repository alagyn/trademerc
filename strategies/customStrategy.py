import cmErrors
from checks.check import Check
from typing import List
from .strategy import *
from indicators import *
from objects.action import *
from objects.stock import *


class CheckList:
    def __init__(self, checks: List[Check] = None):
        self._checks: List[Check] = [] if checks is None else checks

    def addCheck(self, check: Check):
        self._checks.append(check)

    def check(self) -> bool:
        value = True

        for c in self._checks:
            value = value and c.check()

        return value


class StopCalculation:
    def __init__(self, value: ValueFunc, scale: float, limitScale: float):
        self._valF = value
        self._scale = scale
        self._lscale = limitScale

    def __call__(self):
        stop = self._valF() * self._scale
        return stop, stop * self._lscale


class CustomStrategy(Strategy):
    def __init__(self, name: str, symbol: str, enterCond: CheckList, exitCond: CheckList,
                 stopCalc: StopCalculation = None, stopUpdatePeriod=0,
                 inDefAction: Action = ActionEnum.Hold, outDefAction: Action = ActionEnum.Hold):

        super().__init__(symbol, name)

        self.enterCond = enterCond
        self.exitCond = exitCond
        self.stopCalc = stopCalc
        self.stopPeriod = stopUpdatePeriod
        self.nextStop = 0

        self.inDefAction = inDefAction
        self.outDefAction = outDefAction

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

