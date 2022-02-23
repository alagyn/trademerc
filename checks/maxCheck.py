from cmErrors import NotSetupError, CheckError

from checks.check import Check
from objects.strategy_params import NumberParam


class MaxCheck(Check):
    numValFuncs = 1
    params = [NumberParam('maxVal', 'Max', float, 1.0)]


    @classmethod
    def factory(cls, valFuncs, args):
        if len(valFuncs) != 1:
            raise CheckError('Len of val funcs is not 1')

        return MaxCheck(valFuncs[0], args['maxVal'])

    def __init__(self, i, maxVal: float):
        self.i = i
        self.maxVal = maxVal
        self.val = None

    def check(self) -> bool:
        return self.val <= self.maxVal


    def update(self, dry: bool):
        self.val = self.i()
        if self.val is None and not dry:
            raise NotSetupError

