import enum
from abc import ABC
from enum import IntEnum
from typing import Union

class OrderStatus(IntEnum):
    UNFILLED = enum.auto()
    CANCELED = enum.auto()
    FILLED = enum.auto()

class OrderType(IntEnum):
    BUY = enum.auto()
    BUY_AND_STOP = enum.auto()
    SELL = enum.auto()


class Order(ABC):

    def __init__(self, orderid: any):
        self._orderid = orderid

    def orderid(self) -> any:
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
        raise NotImplementedError

    def data(self, key: str) -> any:
        """
        Returns arbitrary data from the wrapped order object
        :param key: The string key
        :return: The data
        """
        raise NotImplementedError

    def orderType(self) -> OrderType:
        raise NotImplementedError

    def symbol(self) -> str:
        raise NotImplementedError

    def qty(self) -> Union[int, None]:
        raise NotImplementedError

    def filledQty(self) -> int:
        raise NotImplementedError

    def filledAvgPrice(self) -> float:
        raise NotImplementedError

    def side(self) -> str:
        if self.orderType() == OrderType.BUY:
            return "buy"

        return "sell"

    def stopPrice(self) -> Union[float, None]:
        raise NotImplementedError

    def limitPrice(self) -> Union[float, None]:
        raise NotImplementedError