from indicators.indicator import Indicator, ValueFunc
from objects.bar import Bar
from objects.strategy_params import DataSelector, NumberParam
from indicators.indicatorManager import HIGH_PRIORITY
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


_SMMA = 'SMMA'


class SMMA(Indicator):
    """Smoothing Moving Average"""

    params = [NumberParam('period', "Period", int, 5),
              DataSelector()]
    outputs = [_SMMA]

    def __init__(self, period: int, data='c'):
        self._data = data
        self._smma = SoloSMMA(period)
        self.avg = ValueFunc(_SMMA)

        super().__init__(HIGH_PRIORITY)

    def addData(self, bar: Bar) -> None:
        if self._data == 'c':
            data = bar.close
        elif self._data == 'l':
            data = bar.lo
        else:
            data = bar.hi

        self.avg.set(self._smma.next(data))

    def setupTime(self) -> int:
        return self._smma.setupTime()
