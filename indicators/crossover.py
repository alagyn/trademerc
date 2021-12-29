from indicators.indicator import Indicator, ValueFunc, MED_PRIORITY

_CO = 'crossover'


class Crossover(Indicator):
    @classmethod
    def getKeys(cls):
        return [_CO]

    def __init__(self, i1: ValueFunc, i2: ValueFunc):
        super().__init__(MED_PRIORITY,
                         {_CO: self.getCrossOver})

        self.i1 = i1
        self.prev1 = None
        self.i2 = i2
        self.prev2 = None

        self._trend = 0

    def addData(self, *, low=None, close=None, high=None) -> None:
        if self.prev1 is None:
            self.prev1 = self.i1()
            self.prev2 = self.i2()
            self._trend = 0

        new1 = self.i1()
        new2 = self.i2()
        out = 0

        # cross down
        if self.prev1 > self.prev2:
            if new1 < new2:
                out = -1.0
        # cross up
        elif new1 > new2:
            out = 1.0

        self.prev1 = new1
        self.prev2 = new2
        self._trend = out

    def getCrossOver(self) -> float:
        return self._trend

    def setupTime(self) -> int:
        return 2
