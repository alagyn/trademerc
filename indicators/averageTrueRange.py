from indicators.indicator import Indicator, ValueFunc, IParam
from indicators.indicatorManager import HIGH_PRIORITY
from indicators.smma import SoloSMMA


class AverageTrueRange(Indicator):
    params = {"period": IParam(int, 5)}
    outputs = ['tr', 'atr']

    def __init__(self, period: int):
        self._p = period

        self._prevClose = None
        self._atr_smma = SoloSMMA(self._p)

        self.tr = ValueFunc('tr')
        self.atr = ValueFunc('atr')

        super().__init__(HIGH_PRIORITY)

    def addData(self, low, close, high) -> None:
        if self._prevClose is None:
            self._prevClose = close
            return

        self.tr.set(max(high, self._prevClose) - min(low, self._prevClose))
        self.atr.set(self._atr_smma.next(self.tr()))

        self._prevClose = close

    def setupTime(self) -> int:
        return self._atr_smma.setupTime() + 1
