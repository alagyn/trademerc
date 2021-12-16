from checks.check import Check
from indicators.indicator import ValueFunc
from cmErrors import NotSetupError


class RangeCheck(Check):
    def __init__(self, i: ValueFunc, minVal: float, maxVal: float):
        self.i = i
        self.minVal = minVal
        self.maxVal = maxVal

    def check(self) -> bool:
        val = self.i()
        if val is None:
            raise NotSetupError

        return self.minVal <= self.i() <= self.maxVal
