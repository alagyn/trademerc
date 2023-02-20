from abc import ABC
from enum import IntEnum
from typing import Union, Any


class OrderStatus(IntEnum):
    UNFILLED = 0
    CANCELED = 1
    FILLED = 2


class OrderType(IntEnum):
    BUY = 0
    BUY_AND_STOP = 1
    SELL = 2


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

    def data(self) -> Any:
        raise NotImplementedError
