from checks.check import Check
from cmErrors import NotSetupError, CheckError
from objects.strategy_params import NumberParam


class MinCheck(Check):
    numValFuncs = 1
    params = [NumberParam('minVal', 'Min', float, 1.0)]

    @classmethod
    def factory(cls, valFuncs, checks, args):
        if len(valFuncs) != 1:
            raise CheckError('Len of val funcs is not 1')

        return MinCheck(valFuncs[0], args['minVal'])

    def __init__(self, i, minVal: float):
        self.i = i
        self.minVal = minVal
        self.val = None

    def check(self) -> bool:
        return self.val >= self.minVal

    def update(self):
        self.val = self.i()
        if self.val is None:
            raise NotSetupError
