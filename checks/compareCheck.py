from .check import Check
from indicators.indicator import ValueFunc
from cmErrors import NotSetupError


class CompareLessThan(Check):
    def __init__(self, i1: ValueFunc, i2: ValueFunc):
        self.i1 = i1
        self.i2 = i2

    def check(self) -> bool:
        val1 = self.i1()
        val2 = self.i2()

        if val1 is None or val2 is None:
            raise NotSetupError

        return val1 < val2


class CompareGreaterThan(Check):
    def __init__(self, i1: ValueFunc, i2: ValueFunc):
        self.i1 = i1
        self.i2 = i2

    def check(self) -> bool:
        val1 = self.i1()
        val2 = self.i2()

        if val1 is None or val2 is None:
            raise NotSetupError

        return val1 > val2

