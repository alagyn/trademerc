from cmErrors import NotSetupError

from checks.check import Check
from indicators.indicator import ValueFunc


class MaxCheck(Check):
    def __init__(self, i: ValueFunc, maxVal: float):
        self.i = i
        self.maxVal = maxVal

    def check(self) -> bool:
        val = self.i()
        if val is None:
            raise NotSetupError
        return self.i() <= self.maxVal
