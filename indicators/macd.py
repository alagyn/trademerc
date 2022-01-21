from indicators.indicator import Indicator, ValueFunc, IParam
from indicators.ema import SoloEMA
from indicators.indicatorManager import HIGH_PRIORITY

_MACD = 'MACD'
_SIGNAL = 'Signal'


class MACD(Indicator):
    """
    Moving Average Convergence Divergence
    """

    params = {'fastPeriod': IParam(int, 5),
              'slowPeriod': IParam(int, 10),
              'sigPeriod': IParam(int, 10)}
    outputs = [_MACD, _SIGNAL]

    def __init__(self, fastPeriod: int, slowPeriod: int, sigPeriod: int):
        self._fp = fastPeriod
        self._sp = slowPeriod
        self._sigP = sigPeriod

        self._fastEMA = SoloEMA(period=fastPeriod)
        self._slowEMA = SoloEMA(period=slowPeriod)
        self._sigEMA = SoloEMA(period=sigPeriod)

        self.macd = ValueFunc(_MACD)
        self.signal = ValueFunc(_SIGNAL)

        super().__init__(HIGH_PRIORITY)

    def addData(self, low, close, high) -> None:
        self._fastEMA.next(close)
        self._slowEMA.next(close)

        fastVal = self._fastEMA.getValue()
        slowVal = self._slowEMA.getValue()

        newMACD = fastVal - slowVal
        self.macd.set(newMACD)

        newSignal = self._sigEMA.next(newMACD)
        self.signal.set(newSignal)

    def setupTime(self) -> int:
        return max(self._fp, self._sp, self._sigP)
