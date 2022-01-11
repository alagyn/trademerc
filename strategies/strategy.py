from objects.stock import Stock
from objects.action import Action


class Strategy:
    def __init__(self, symbol: str, name: str):
        self.symbol = symbol
        self.name = name

    def getName(self):
        return self.name

    def nextAction(self, day: int, stock: Stock) -> Action:
        raise NotImplementedError

    def dryRun(self) -> None:
        raise NotImplementedError
