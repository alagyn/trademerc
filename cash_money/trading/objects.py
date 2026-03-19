from enum import IntEnum
import enum
from typing import Optional, Tuple
import datetime
from collections import deque

from abc import ABC
from enum import IntEnum
from typing import Union, Any


class Bar:

    def __init__(self, lo: float, close: float, hi: float, vol: float, date: datetime.datetime):
        self.lo = lo
        self.close = close
        self.hi = hi
        self.vol = vol
        self.date: datetime.datetime = date

    def __str__(self) -> str:
        return f"(L:{self.lo}, C:{self.close}, H:{self.hi}, V:{self.vol})"


class OrderStatus(IntEnum):
    UNFILLED = 0
    CANCELED = 1
    FILLED = 2
    REPLACED = 3


class OrderType(IntEnum):
    BUY = enum.auto()
    SELL = enum.auto()
    STOP = enum.auto()


class Order(ABC):

    def __init__(self, orderid: Any):
        self._orderid = orderid

    def orderid(self) -> Any:
        """
        Returns this order's id
        :return: the id
        """
        return self._orderid

    def status(self) -> OrderStatus:
        """
        Returns the status of the order
        :return:
        """
        raise NotImplementedError()

    def orderType(self) -> OrderType:
        raise NotImplementedError()

    def symbol(self) -> str:
        raise NotImplementedError()

    def qty(self) -> Union[int, None]:
        raise NotImplementedError()

    def filledQty(self) -> int:
        raise NotImplementedError()

    def filledAvgPrice(self) -> float:
        raise NotImplementedError()

    def side(self) -> str:
        if self.orderType() == OrderType.BUY:
            return "buy"

        return "sell"

    def stopPrice(self) -> Union[float, None]:
        raise NotImplementedError()

    def limitPrice(self) -> Union[float, None]:
        raise NotImplementedError()

    def data(self) -> Any:
        raise NotImplementedError()

    def timestamp(self) -> datetime.datetime:
        raise NotImplementedError()


class StockStatus(IntEnum):
    InMarket = 0
    Pending = 1
    OutMarket = 2


class CMPosition:

    def getstatus(self) -> StockStatus:
        raise NotImplementedError()

    def data(self) -> Any:
        raise NotImplementedError()

    def qty(self) -> int:
        raise NotImplementedError()


class Stock:

    def __init__(self, symbol: str):
        self.symbol: str = symbol
        self.buyOrder: Optional[Order] = None
        self.sellOrder: Optional[Order] = None
        self.stopOrder: Optional[Order] = None
        self.buyDate: Optional[datetime.date] = None

        self.position: Optional[CMPosition] = None

        self.bar: Optional[Bar] = None

        self.lastStopUpdate: Optional[datetime.date] = None
        self.nextStopUpdate: Optional[datetime.date] = None

        # Trader will add a new entry every day,
        # len == 2, after two days the unsettled funds will
        # be popped
        self.unsettledFunds = deque(maxlen=2)
        self.unsettledFunds.append(0)
        # Acts the same as the unsettled funds
        # Keeps track of day trades specific to this stock
        self.dayTrades = deque(maxlen=5)
        self.dayTrades.append(0)

    def updateBar(self, bar: Optional[Bar]):
        self.bar = bar

    def status(self) -> StockStatus:
        if self.position is None:
            return StockStatus.OutMarket
        else:
            return self.position.getstatus()

    def setNextStopDate(self, date: datetime.datetime):
        self.nextStopUpdate = date

    def updateBuyDate(self, date: datetime.date):
        self.buyDate = date


class ActionEnum(IntEnum):
    Buy = enum.auto()
    Sell = enum.auto()
    HoldInMarket = enum.auto()
    HoldOutMarket = enum.auto()
    UpdateStop = enum.auto()


class Action:

    def _init(self, stock: 'Stock', action: ActionEnum):
        self.stock = stock
        self.action = action

    def __init__(self):
        """
        Do not allow this to be instantiated
        """
        raise NotImplementedError

    def _str_args(self) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return f"Action: {self.action.name}, Symbol: {self.stock.symbol}{self._str_args()}"


class BuyAction(Action):

    def __init__(self, stock: 'Stock', stopPrice: Optional[float] = None):
        self._init(stock, ActionEnum.Buy)
        self.stopPrice = stopPrice

    def _str_args(self) -> str:
        return f", stop-price: {self.stopPrice}"


class SellAction(Action):

    def __init__(self, stock: 'Stock'):
        self._init(stock, ActionEnum.Sell)


class UpdateStopAction(Action):

    def __init__(self, stock: 'Stock', stopPrice: float):
        self._init(stock, ActionEnum.UpdateStop)
        self.stopPrice = stopPrice

    def _str_args(self) -> str:
        return f", stop-price: {self.stopPrice}"


class HoldAction(Action):

    def __init__(self, stock: 'Stock'):
        if stock.status() == StockStatus.InMarket:
            self._init(stock, ActionEnum.HoldInMarket)
        else:
            self._init(stock, ActionEnum.HoldOutMarket)
