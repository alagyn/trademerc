from enum import IntEnum
import enum


class ActionEnum(IntEnum):
    BuyAndStop = enum.auto()
    Buy = enum.auto()
    Sell = enum.auto()
    Hold = enum.auto()
    UpdateStop = enum.auto()


class Action:
    def __init__(self, stock, action: ActionEnum, **kwargs):
        self.stock = stock
        self.action = action
        self.args = kwargs

    def __str__(self):
        if len(self.args) > 0:
            a = f", Args: {self.args}"
        else:
            a = ""

        return f'Sym: {self.stock.symbol}: {self.action.name}{a}'
