from .check import Check
from cmErrors import CheckError


class CrossoverCheck(Check):
    @classmethod
    def factory(cls, valFuncs, checks, args):
        if len(valFuncs) != 2:
            raise CheckError('Len of checks not equal to 2')

        return CrossoverCheck(valFuncs[0], valFuncs[1], args['direct'])


    def __init__(self, i1, i2, direct: str):
        self.direct = True if direct == 'up' else False
        self.i1 = i1
        self.i2 = i2

        self.prevDiff = None

    def check(self) -> bool:
        if self.prevDiff is None:
            self.prevDiff = self.i1() - self.i2()
            return False

        out = False

        diff = self.i1() - self.i2()

        upcross = 1 if self.prevDiff < 0 and diff > 0 else 0
        downcross = 1 if self.prevDiff > 0 and diff < 0 else 0

        cross = upcross - downcross

        # cross up
        if self.direct and cross > 0:
            out = True
        # cross down
        elif not self.direct and cross < 0:
            out = True

        self.prevDiff = diff

        return out
