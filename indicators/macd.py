from indicators.indicator import Indicator, HIGH_PRIORITY
from indicators.ema import SoloEMA


# Moving Average Convergence Divergence
class MACD(Indicator):
    def __init__(self, fastPeriod: int, slowPeriod: int, sigPeriod: int):
        super().__init__(HIGH_PRIORITY,
                         {
                             'signal': self.getSignal,
                             'macd': self.getMACD
                         })

        self._fp = fastPeriod
        self._sp = slowPeriod
        self._sigP = sigPeriod

        self.fastEMA = SoloEMA(period=fastPeriod)
        self.slowEMA = SoloEMA(period=slowPeriod)
        self.sigEMA = SoloEMA(period=sigPeriod)

        self.macd = 0


    def addData(self, *, low=None, close=None, high=None) -> None:
        self.fastEMA.next(close)
        self.slowEMA.next(close)

        fastVal = self.fastEMA.getValue()
        slowVal = self.slowEMA.getValue()
        self.macd = slowVal - fastVal
        self.sigEMA.next(self.macd)


    def getSignal(self) -> float:
        return self.sigEMA.getValue()

    def getMACD(self) -> float:
        return self.macd

    def setupTime(self) -> int:
        return max(self._fp, self._sp, self._sigP)

