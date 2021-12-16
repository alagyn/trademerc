from checks.check import Check
from indicators.indicator import ValueFunc
from cmErrors import NotSetupError


class MinCheck(Check):
    def __init__(self, i: ValueFunc, minVal: float):
        self.i = i
        self.minVal = minVal

    def check(self) -> bool:
        val = self.i()
        if val is None:
            raise NotSetupError
        return self.i() >= self.minVal
