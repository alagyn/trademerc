from objects.stock import Stock
from objects.action import Action


class Strategy:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def nextAction(self, day: int, stock: Stock) -> Action:
        raise NotImplementedError
