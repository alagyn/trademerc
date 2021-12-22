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
        self.buyDate = ''

        self.initBuyPower = 0
        self.buyPower = 0
        self.activeOrder = None
        self.position = None

        self.bar = None

    def updateBar(self, bar):
        self.bar = bar

    def updatePosition(self, newPos):
        if self.position is None:
            self.buyPower -= newPos.cost_basis

        self.position = newPos

    def addToPot(self, amnt):
        self.buyPower += amnt

    def status(self) -> StockStatus:
        if self.position is None:
            return StockStatus.OutMarket
        else:
            return StockStatus.InMarket
