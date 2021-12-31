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
        self.prev1 = None
        self.i2 = i2
        self.prev2 = None

    def check(self) -> bool:
        if self.prev1 is None:
            self.prev1 = self.i1()
            self.prev2 = self.i2()
            return False

        new1 = self.i1()
        new2 = self.i2()
        out = False

        # cross up
        if self.direct:
            if self.prev1 < self.prev2 and new1 > new2:
                out = True
        # cross down
        else:
            if self.prev1 > self.prev2 and new1 < new2:
                out = True

        self.prev1 = new1
        self.prev2 = new2

        return out
