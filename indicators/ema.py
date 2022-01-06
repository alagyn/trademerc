from indicators.indicator import Indicator, HIGH_PRIORITY, ValueFunc
from cmErrors import IndicatorError


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



class EMA(Indicator):
    """
    Exponential Moving Average
    """


    def __init__(self, period: int, smoothing: int = 2, data='c'):
        super().__init__(HIGH_PRIORITY)

        self.data = data
        self.ema = SoloEMA(smoothing=smoothing, period=period)
        self.avg = 0

    def addData(self, low, close, high) -> float:
        if self.data == 'c':
            self.avg = self.ema.next(close)
        elif self.data == 'l':
            self.avg = self.ema.next(low)
        else:
            self.avg = self.ema.next(high)

        return self.avg

    @ValueFunc(key='ema')
    def getValue(self) -> float:
        return self.avg

    def setupTime(self) -> int:
        return 2
