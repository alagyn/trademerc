from enum import IntEnum
import enum
from typing import Optional

from .action import Action, ActionEnum
import datetime
from consts import DATE_FMT
from objects.order import Order
from objects.bar import Bar


class StockStatus(IntEnum):
    InMarket = enum.auto()
    Pending = enum.auto()
    OutMarket = enum.auto()


class Stock:
    def __init__(self, symbol: str):
        self.symbol: str = symbol
        self._order: Optional[Order] = None
        self._stopOrder: Optional[Order] = None
        self.buyDate = ''

        self.position = None

        self.bar: Optional[Bar] = None

        self.lastCloseOrder = None

        self.lastStopUpdate = None
        self.nextStopUpdate = None

    def updateBar(self, bar: Bar):
        self.bar = bar

    def order(self, o: Order = None) -> Order:
        if o is not None:
            self._order = o

        return self._order

    def stopOrder(self, so: Order = None) -> Order:
        if so is not None:
            self._stopOrder = so

        return self._stopOrder

    def status(self) -> StockStatus:
        if self.position is None:
            return StockStatus.OutMarket
        else:
            return StockStatus.InMarket

    def buyAndStop(self, stopPrice: float, limitPrice: float):
        """Creates a buy action for this stock"""
        return Action(self, ActionEnum.BuyAndStop,
                      stopPrice=round(stopPrice, 2),
                      limitPrice=round(limitPrice, 2))

    def buy(self):
        return Action(self, ActionEnum.Buy)

    def sell(self):
        """Creates a sell action for this stock"""
        return Action(self, ActionEnum.Sell)

    def updateStop(self, stopPrice: float, limitPrice: float):
        """Creates a stop update action for this stock"""
        self.lastStopUpdate = datetime.datetime.today().strftime(DATE_FMT)
        return Action(self, ActionEnum.UpdateStop,
                      stopPrice=round(stopPrice, 2),
                      limitPrice=round(limitPrice, 2))

    def setNextStopDate(self, delta: int):
        date = datetime.datetime.today() + datetime.timedelta(delta)
        self.nextStopUpdate = date.strftime(DATE_FMT)