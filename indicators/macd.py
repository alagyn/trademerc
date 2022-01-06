from indicators.indicator import Indicator, HIGH_PRIORITY, ValueFunc
from indicators.ema import SoloEMA


class MACD(Indicator):
    """
    Moving Average Convergence Divergence
    """
    def __init__(self, fastPeriod: int, slowPeriod: int, sigPeriod: int):
        super().__init__(HIGH_PRIORITY)

        self._fp = fastPeriod
        self._sp = slowPeriod
        self._sigP = sigPeriod

        self.fastEMA = SoloEMA(period=fastPeriod)
        self.slowEMA = SoloEMA(period=slowPeriod)
        self.sigEMA = SoloEMA(period=sigPeriod)

        self.macd = 0

    def addData(self, low, close, high) -> None:
        self.fastEMA.next(close)
        self.slowEMA.next(close)

        fastVal = self.fastEMA.getValue()
        slowVal = self.slowEMA.getValue()
        self.macd = slowVal - fastVal
        self.sigEMA.next(self.macd)

    @ValueFunc(key='signal')
    def getSignal(self) -> float:
        return self.sigEMA.getValue()

    @ValueFunc(key='macd')
    def getMACD(self) -> float:
        return self.macd

    def setupTime(self) -> int:
        return max(self._fp, self._sp, self._sigP)
