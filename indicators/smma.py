from indicators.indicator import Indicator, HIGH_PRIORITY
from indicators.ema import SoloEMA


class SoloSMMA:
    def __init__(self, period: int):
        self._a = 1 / period
        self._smma = SoloEMA(alpha=self._a)
        self._c = 0
        self._tempSum = 0
        self._p = period

    def next(self, data) -> float:
        if self._c < self._p:
            self._tempSum += data
            self._c += 1

        if self._c >= self._p:
            self._smma.next(data)

        return self._smma.getValue()

    def getValue(self) -> float:
        return self._smma.getValue()

    def setupTime(self) -> int:
        return self._p


class SMMA(Indicator):
    def __init__(self, period: int, value='c'):
        super().__init__(HIGH_PRIORITY)

        self._value = value
        self._smma = SoloSMMA(period)

    def addData(self, *, low=None, close=None, high=None) -> None:
        if self._value == 'c':
            data = close
        elif self._value == 'l':
            data = low
        else:
            data = high

        self._smma.next(data)

    def getAvg(self):
        return self._smma.getValue()

    def setupTime(self) -> int:
        return self._smma.setupTime()
