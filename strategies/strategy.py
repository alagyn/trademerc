from enum import IntEnum
import enum
from stock import Stock


class ActionEnum(IntEnum):
    Buy = enum.auto()
    Sell = enum.auto()
    Hold = enum.auto()
    UpdateStop = enum.auto()


class Action:
    def __init__(self, stock: Stock, action: ActionEnum, **kwargs):
        self.stock = stock
        self.action = action
        self.args = kwargs

    def __str__(self):
        return f'Action: {self.action.name}, Args: {self.args}'


class Strategy:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def nextAction(self, day: int, stock: Stock) -> Action:
        raise NotImplementedError
