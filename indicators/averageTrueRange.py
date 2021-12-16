from indicators.indicator import Indicator, HIGH_PRIORITY
from indicators.smma import SoloSMMA


class AverageTrueRange(Indicator):
    def __init__(self, period: int):
        super().__init__(HIGH_PRIORITY)

        self.p = period

        self.tr = None
        self.prevClose = None

        self._vals = []

        self.atr_smma = SoloSMMA(self.p)

    def addData(self, *, low=None, close=None, high=None) -> None:
        if self.prevClose is None:
            self.prevClose = close
            return

        self.tr = max(high, self.prevClose) - min(low, self.prevClose)

        self.atr_smma.next(self.tr)

    def getATR(self):
        return self.atr_smma.getValue()

    def getTR(self):
        return self.tr

    def setupTime(self) -> int:
        return self.atr_smma.setupTime()
