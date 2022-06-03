from typing import List

from cash_money.checks.check import CheckParent
from .strategy import *
from cash_money.objects.action import ActionEnum
from cash_money.objects.stock import StockStatus


class CheckList:
    def __init__(self, checks: List[CheckParent] = None):
        self._checks: List[CheckParent] = [] if checks is None else checks

    def addCheck(self, c: CheckParent):
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

    def __call__(self, close):
        stop = close - (self._valF() * self._scale)
        return stop, stop * self._lscale


class CustomStrategy(Strategy):
    def __init__(self, name: str, symbol: str, iManage: IndicatorManager, cManage: CheckManager,
                 enterCond: CheckParent,
                 exitCond: CheckParent,
                 stopCalc: StopCalculation = None, stopUpdatePeriod=0):

        super().__init__(symbol, name, iManage, cManage)

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
                stop, limit = self.stopCalc(self.bar.close)
                return stock.updateStop(stop, limit)

            return Action(stock, ActionEnum.HoldInMarket)

        # Out Market
        elif pos == StockStatus.OutMarket:
            if self.enterCond.check():
                self.nextStop = day + self.stopPeriod
                if self.stopCalc is not None:
                    stop, limit = self.stopCalc(self.bar.close)
                    return stock.buyAndStop(stop, limit)
                else:
                    return stock.buy()

            return Action(stock, ActionEnum.HoldOutMarket)
