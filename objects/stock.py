from enum import IntEnum
import enum
from .action import Action, ActionEnum


class StockStatus(IntEnum):
    InMarket = enum.auto()
    Pending = enum.auto()
    OutMarket = enum.auto()


class Stock:
    def __init__(self, symbol: str):
        self.symbol: str = symbol
        self.order = None
        self.stopOrder = None
        self.buyDate = ''

        self.activeOrder = None
        self.position = None

        self.bar = None

    def updateBar(self, bar):
        self.bar = bar

    def status(self) -> StockStatus:
        if self.position is None:
            return StockStatus.OutMarket
        else:
            return StockStatus.InMarket

    def buyAndStop(self, stopPrice: float, limitPrice: float):
        """Creates a buy action for this stock"""
        return Action(self, ActionEnum.BuyAndStop, stopPrice=stopPrice, limitPrice=limitPrice)

    def buy(self):
        return Action(self, ActionEnum.Buy)

    def sell(self):
        """Creates a sell action for this stock"""
        return Action(self, ActionEnum.Sell)

    def updateStop(self, stopPrice: float, limitPrice: float):
        """Creates a stop update action for this stock"""
        return Action(self, ActionEnum.UpdateStop, stopPrice=stopPrice, limitPrice=limitPrice)

