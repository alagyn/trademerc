from .check import Check
from cmErrors import NotSetupError, CheckError


class CompareLessThan(Check):
    def __init__(self, i1, i2):
        self.i1 = i1
        self.i2 = i2

    def check(self) -> bool:
        val1 = self.i1()
        val2 = self.i2()

        if val1 is None or val2 is None:
            raise NotSetupError

        return val1 < val2

    @classmethod
    def factory(cls, valFuncs, checks, args):
        if len(valFuncs) != 2:
            raise CheckError('Len of value funcs is not 2')

        return CompareLessThan(*valFuncs)


class CompareGreaterThan(Check):
    def __init__(self, i1, i2):
        self.i1 = i1
        self.i2 = i2

    def check(self) -> bool:
        val1 = self.i1()
        val2 = self.i2()

        if val1 is None or val2 is None:
            raise NotSetupError

        return val1 > val2

    @classmethod
    def factory(cls, valFuncs, checks, args):
        if len(valFuncs) != 2:
            raise CheckError('Len of value funcs is not 2')

        return CompareLessThan(*valFuncs)