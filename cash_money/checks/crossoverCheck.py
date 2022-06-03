
from cash_money.objects.strategy_params import ComboSelector
from .check import Check
from cash_money.cmErrors import CheckError, NotSetupError


class CrossoverCheck(Check):
    numValFuncs = 2
    params = [ComboSelector('direct', 'Direction', ['up', 'down'], 'up')]

    @classmethod
    def factory(cls, valFuncs, args):
        if len(valFuncs) != 2:
            raise CheckError('Len of checks not equal to 2')

        return CrossoverCheck(valFuncs[0], valFuncs[1], args['direct'])

    def __init__(self, i1, i2, direct: str):
        self.direct = True if direct == 'up' else False
        self.i1 = i1
        self.i2 = i2

        self.prevDiff = None
        self.curDiff = None

    def update(self, dry: bool):
        val1 = self.i1()
        val2 = self.i2()

        if val1 is None or val2 is None:
            if dry:
                return

            raise NotSetupError

        if self.curDiff is None:
            self.curDiff = self.i1() - self.i2()
            return

        self.prevDiff = self.curDiff
        self.curDiff = self.i1() - self.i2()


    def check(self) -> bool:
        if self.prevDiff is None or self.curDiff is None:
            raise NotSetupError

        upcross = self.prevDiff < 0 < self.curDiff
        downcross = self.prevDiff > 0 > self.curDiff

        return (self.direct and upcross) or (not self.direct and downcross)
