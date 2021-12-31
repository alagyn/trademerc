from checks.check import Check
from cmErrors import NotSetupError, CheckError


class MinCheck(Check):
    @classmethod
    def factory(cls, valFuncs, checks, args):
        if len(valFuncs) != 1:
            raise CheckError('Len of val funcs is not 1')

        return MinCheck(valFuncs[0], args['minVal'])

    def __init__(self, i, minVal: float):
        self.i = i
        self.minVal = minVal

    def check(self) -> bool:
        val = self.i()
        if val is None:
            raise NotSetupError
        return self.i() >= self.minVal
