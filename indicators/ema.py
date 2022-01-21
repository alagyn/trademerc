from indicators.indicator import Indicator, ValueFunc, IParam, DataSelector
from cmErrors import IndicatorError
from indicators.indicatorManager import HIGH_PRIORITY


class SoloEMA:
    def __init__(self, *, alpha: float = None, period: float = None, smoothing: float = 2):
        self._avg = None
        if alpha is not None:
            self._a = alpha
        elif period is None or smoothing is None:
            raise IndicatorError('Alpha or period and smoothing not supplied')
        else:
            self._a = smoothing / (period + 1)

        self._ia = 1 - self._a

    def next(self, data) -> float:
        if self._avg is None:
            self._avg = data
        else:
            self._avg = data * self._a + self._avg * self._ia
        return self._avg

    def getValue(self) -> float:
        return self._avg


_EMA = 'EMA'


class EMA(Indicator):
    """
    Exponential Moving Average
    """
    params = {'period': IParam(int, 5),
              'smoothing': IParam(int, 2),
              'data': DataSelector()}


    def __init__(self, period: int, smoothing: int = 2, data='c'):
        self._data = data
        self._ema = SoloEMA(smoothing=smoothing, period=period)
        self.avg = ValueFunc(_EMA)

        super().__init__(HIGH_PRIORITY)

    def addData(self, low, close, high):
        if self._data == 'c':
            out = self._ema.next(close)
        elif self._data == 'l':
            out = self._ema.next(low)
        else:
            out = self._ema.next(high)

        self.avg.set(out)

    def setupTime(self) -> int:
        return 2
