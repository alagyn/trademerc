from enum import IntEnum
import enum


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
