from indicators.indicator import Indicator, HIGH_PRIORITY, ValueFunc
from indicators.ema import SoloEMA


class MACD(Indicator):
    """
    Moving Average Convergence Divergence
    """

    def __init__(self, fastPeriod: int, slowPeriod: int, sigPeriod: int):
        self._fp = fastPeriod
        self._sp = slowPeriod
        self._sigP = sigPeriod

        self._fastEMA = SoloEMA(period=fastPeriod)
        self._slowEMA = SoloEMA(period=slowPeriod)
        self._sigEMA = SoloEMA(period=sigPeriod)

        self.macd = ValueFunc('macd')
        self.signal = ValueFunc('signal')

        super().__init__(HIGH_PRIORITY)

    def addData(self, low, close, high) -> None:
        self._fastEMA.next(close)
        self._slowEMA.next(close)

        fastVal = self._fastEMA.getValue()
        slowVal = self._slowEMA.getValue()

        newMACD = slowVal - fastVal
        self.macd.set(newMACD)

        newSignal = self._sigEMA.next(newMACD)
        self.signal.set(newSignal)

    def setupTime(self) -> int:
        return max(self._fp, self._sp, self._sigP)
