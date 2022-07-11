import datetime
from enum import IntEnum
from typing import Optional
import abc

from cash_money.consts import DATE_FMT
from cash_money.objects.bar import Bar
from cash_money.objects.order import Order
from .action import Action, ActionEnum


class StockStatus(IntEnum):
    InMarket = 0
    Pending = 1
    OutMarket = 2

class CMPosition(abc.ABC):
    @abc.abstractmethod
    def getstatus(self) -> StockStatus:
        raise NotImplementedError

    @abc.abstractmethod
    def data(self) -> any:
        raise NotImplementedError

class Stock:
    def __init__(self, symbol: str):
        self.symbol: str = symbol
        self.order: Optional[Order] = None
        self.stopOrder: Optional[Order] = None
        self.buyDate = ''

        self.position: Optional[CMPosition] = None

        self.bar: Optional[Bar] = None

        self.lastCloseOrder = None

        self.lastStopUpdate = None
        self.nextStopUpdate = None

    def updateBar(self, bar: Bar):
        self.bar = bar

    def status(self) -> StockStatus:
        if self.position is None:
            return StockStatus.OutMarket
        else:
            return self.position.getstatus()

    def buyAndStop(self, stopPrice: float, limitPrice: float):
        """Creates a buy action for this stock"""
        return Action(self, ActionEnum.BuyAndStop,
                      stopPrice=round(stopPrice, 2),
                      limitPrice=round(limitPrice, 2))

    def hold(self):
        if self.status() == StockStatus.InMarket:
            return Action(self, ActionEnum.HoldInMarket)
        else:
            return Action(self, ActionEnum.HoldOutMarket)

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
