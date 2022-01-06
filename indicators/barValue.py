from indicators.indicator import Indicator, HIGH_PRIORITY, ValueFunc


class BarValue(Indicator):

    def __init__(self):
        super(BarValue, self).__init__(HIGH_PRIORITY)
        self.lo = 0
        self.closeVal = 0
        self.hi = 0

    def addData(self, low, close, high) -> None:
        self.lo = low
        self.closeVal = close
        self.hi = high

    def setupTime(self) -> int:
        return 1

    @ValueFunc(key='low')
    def low(self) -> float:
        return self.lo

    @ValueFunc(key='close')
    def close(self) -> float:
        return self.closeVal

    @ValueFunc(key='high')
    def high(self) -> float:
        return self.hi
