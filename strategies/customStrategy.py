from checks.check import Check
from typing import List
from .strategy import *
from objects.action import *


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


class CustomStrategy(Strategy):
    def __init__(self, symbol: str, buyStrat: CheckList, sellStrat: CheckList,
                 inDefAction: Action = ActionEnum.Hold, outDefAction: Action = ActionEnum.Hold):
        super().__init__(symbol)

        self.buyStrat = buyStrat
        self.sellStrat = sellStrat
        self.inDefAction = inDefAction
        self.outDefAction = outDefAction

    def nextAction(self, day: int, stock: Stock) -> Action:
        bVal = self.buyStrat.check()
        sVal = self.buyStrat.check()

        """
        if pos == Position.InMarket:
            if bVal and sVal:
                return self.inDefAction

            if sVal:
                return Action.Sell

        elif pos == Position.OutMarket:
            if bVal and sVal:
                return self.outDefAction

            if bVal:
                return Action.Buy

        return Action.Hold
        """
        raise NotImplementedError()
