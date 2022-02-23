from objects.strategy_params import ComboSelector
from .check import Check
from cmErrors import NotSetupError, CheckError
from operator import lt, gt


class Compare(Check):
    numValFuncs = 2
    params = [ComboSelector('op', 'Type', ['<', '>'], '<')]

    def __init__(self, i1, i2, op: str):
        self.i1 = i1
        self.i2 = i2

        if op == '<':
            self.op = lt
        else:
            self.op = gt

        self.val1 = None
        self.val2 = None

    def update(self):
        self.val1 = self.i1()
        self.val2 = self.i2()

        if self.val1 is None or self.val2 is None:
            raise NotSetupError


    def check(self) -> bool:
        return self.op(self.val1, self.val2)

    @classmethod
    def factory(cls, valFuncs, checks, args):
        if len(valFuncs) != 2:
            raise CheckError('Len of value funcs is not 2')

        if 'op' not in args:
            raise CheckError('Missing operator param')

        op = args['op']
        if op == '<' or op == '>':
            return Compare(*valFuncs, op)
