from cmErrors import NotSetupError, CheckError

from checks.check import Check


class MaxCheck(Check):
    @classmethod
    def factory(cls, valFuncs, checks, args):
        if len(valFuncs) != 1:
            raise CheckError('Len of val funcs is not 1')

        return MaxCheck(valFuncs[0], args['maxVal'])

    def __init__(self, i, maxVal: float):
        self.i = i
        self.maxVal = maxVal

    def check(self) -> bool:
        val = self.i()
        if val is None:
            raise NotSetupError
        return val <= self.maxVal

    def update(self) -> bool:
        return self.check()
