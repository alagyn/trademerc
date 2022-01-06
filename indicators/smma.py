from indicators.indicator import Indicator, HIGH_PRIORITY, ValueFunc
from indicators.ema import SoloEMA


class SoloSMMA:
    """
    SMMA is equivalent to an EMA with alpha = 1/period
    """

    def __init__(self, period: int):
        self._a = 1 / period
        self._ema = SoloEMA(alpha=self._a)
        self._p = period

    def next(self, data) -> float:
        return self._ema.next(data)

    def getValue(self) -> float:
        return self._ema.getValue()

    def setupTime(self) -> int:
        return self._p


_SMMA = 'smma'


class SMMA(Indicator):
    """Smoothing Moving Average"""

    def __init__(self, period: int, value='c'):
        self._value = value
        self._smma = SoloSMMA(period)
        self.avg = ValueFunc('smma')

        super().__init__(HIGH_PRIORITY)

    def addData(self, low, close, high) -> None:
        if self._value == 'c':
            data = close
        elif self._value == 'l':
            data = low
        else:
            data = high

        self.avg.set(self._smma.next(data))

    def setupTime(self) -> int:
        return self._smma.setupTime()
