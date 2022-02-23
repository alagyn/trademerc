from checks.check import Check
from cmErrors import NotSetupError, CheckError
from objects.strategy_params import NumberParam


class RangeCheck(Check):
    numValFuncs = 1
    params = [NumberParam('minVal', 'Min', float, 1.0),
              NumberParam('maxVal', 'Max', float, 1.0)]

    @classmethod
    def factory(cls, valFuncs, args):
        if len(valFuncs) != 1:
            raise CheckError('Len of val funcs is not 1')

        return RangeCheck(valFuncs[0], args['minVal'], args['maxVal'])

    def __init__(self, i, minVal: float, maxVal: float):
        self.i = i
        self.minVal = minVal
        self.maxVal = maxVal
        self.val = None

    def check(self) -> bool:
        return self.minVal <= self.val <= self.maxVal

    def update(self, dry: bool):
        self.val = self.i()
        if self.val is None and not dry:
            raise NotSetupError
