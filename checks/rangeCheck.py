from checks.check import Check
from cmErrors import NotSetupError, CheckError


class RangeCheck(Check):
    @classmethod
    def factory(cls, valFuncs, checks, args):
        if len(valFuncs) != 1:
            raise CheckError('Len of val funcs is not 1')

        return RangeCheck(valFuncs[0], args['minVal'], args['maxVal'])

    def __init__(self, i, minVal: float, maxVal: float):
        self.i = i
        self.minVal = minVal
        self.maxVal = maxVal

    def check(self) -> bool:
        val = self.i()
        if val is None:
            raise NotSetupError

        return self.minVal <= self.i() <= self.maxVal

    def update(self) -> bool:
        return self.check()