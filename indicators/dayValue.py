from indicators.indicator import Indicator, HIGH_PRIORITY


class DayValue(Indicator):
    def __init__(self):
        super(DayValue, self).__init__(HIGH_PRIORITY)
        self.lo = 0
        self.closeVal = 0
        self.hi = 0

    def addData(self, *, low=None, close=None, high=None) -> None:
        self.lo = low
        self.closeVal = close
        self.hi = high

    def setupTime(self) -> int:
        return 1

    def low(self) -> float:
        return self.lo

    def close(self) -> float:
        return self.closeVal

    def high(self) -> float:
        return self.hi