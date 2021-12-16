import enum

from checks.check import Check
from typing import List
from enum import IntEnum


class Position(IntEnum):
    InMarket = enum.auto()
    OutMarket = enum.auto()


class Strategy:
    def __init__(self, checks: List[Check] = None):
        self._checks: List[Check] = [] if checks is None else checks

    def addCheck(self, check: Check):
        self._checks.append(check)

    def check(self) -> bool:
        value = True

        for c in self._checks:
            value = value and c.check()

        return value


class Action(IntEnum):
    Buy = enum.auto()
    Sell = enum.auto()
    Hold = enum.auto()


class Broker:
    def __init__(self, buyStrat: Strategy, sellStrat: Strategy,
                 defaultAction: Action = Action.Hold):
        self.buyStrat = buyStrat
        self.sellStrat = sellStrat
        self.defAction = defaultAction

    def next(self, pos: Position) -> Action:
        bVal = self.buyStrat.check()
        sVal = self.buyStrat.check()

        if bVal and sVal:
            return self.defAction
        elif bVal:
            return Action.Buy
        elif sVal:
            return Action.Sell

        return Action.Hold


