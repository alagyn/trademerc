from abc import ABC
from typing import List, Dict, Union, Tuple

from objects.order import Order
from objects.bar import Bar
from objects.stock import Stock
from objects.position import Position


class Broker(ABC):
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.stocks = {}

        # Dict of symb->stock
        self.stocks = {}
        for x in self.symbols:
            self.stocks[x] = Stock(x)

        self.tradeDay = 0

    def incDay(self):
        self.tradeDay += 1

    def preRun(self):
        """
        Called once before any trades occur
        :return:
        """
        raise NotImplementedError

    def preTrade(self) -> bool:
        """
        Called before the trader is run, all relevant data is updated for the trader to use
        :return: true if run should continue, else false
        """
        raise NotImplementedError

    def postTrade(self) -> None:
        """
        Called after the trader is run
        :return: None
        """
        raise NotImplementedError

    def postRun(self) -> None:
        """
        Called after run is complete, prior to exit
        :return: None
        """
        raise NotImplementedError

    def buyPwr(self) -> float:
        """
        Returns the account's current buying power
        :return: the buying power
        """
        raise NotImplementedError

    def getSetupBars(self, setupTime: int) -> Dict[str, List[Bar]]:
        """
        Returns stock bars for the requested setup time
        :param setupTime: The number of days needed to setup
        :return: The bars
        """
        raise NotImplementedError

    def cancelAllOrders(self) -> None:
        """
        Cancels all unfilled orders
        :return: None
        """
        raise NotImplementedError

    def closeAllPositions(self) -> None:
        """
        Closes all open positions
        :return: None
        """
        raise NotImplementedError

    def getOrder(self, orderid: int) -> Order:
        """
        Returns the order for the given id
        :param orderid: The order's id
        :return: The order
        """
        raise NotImplementedError

    def getAllOrders(self) -> List[Order]:
        """
        Returns a list of all open orders
        :return: The orders
        """
        raise NotImplementedError

    def getPosition(self, symbol: str) -> Position:
        """
        Returns the position for the passed symbol, or None
        :param symbol: the position or None
        :return:
        """
        raise NotImplementedError

    def getOpenPositions(self) -> Dict[str, Position]:
        """
        Returns a dict of all open positions
        :return: the positions
        """
        raise NotImplementedError

    def submitBuy(self, stock: Stock, qty: int,
                  stopLimit: Union[Tuple[float, float], None] = None) -> None:
        """
        Submits a buy order for the given symbol and quantity
        :param stock: The stock to buy
        :param qty: The quantity to buy
        :param stopLimit: An optional tuple to place a stop-limit order [stop, limit]
        :return: The new order
        """
        raise NotImplementedError

    def closePosition(self, stock: Stock) -> None:
        """
        Closes a position and sells all shares at current market price
        :param stock: The stock
        :return: None
        """
        raise NotImplementedError

    def submitSell(self, symbol: str, qty: int) -> Order:
        """
        Sumbits a sell order for the given symbol and quantity
        :param symbol: The symbol
        :param qty: The quantity
        :return: The sell order
        """
        raise NotImplementedError

    def submitUpdateStop(self, stock: Stock, stopLimit: Union[Tuple[float, float], None]) -> None:
        """
        Replaces an existing stop order
        :param stock: The stock
        :param stopLimit: A tuple to place a stop-limit order [stop, limit]
        :return: The new order
        """
        raise NotImplementedError
