from indicators.indicator import Indicator, ValueFunc
from objects.bar import Bar
from objects.strategy_params import NumberParam
from indicators.indicatorManager import HIGH_PRIORITY
from indicators.smma import SoloSMMA


class AverageTrueRange(Indicator):
    params = [NumberParam("period", "Period", int, 5)]
    outputs = ['tr', 'atr']

    def __init__(self, period: int):
        self._p = period

        self._prevClose = None
        self._atr_smma = SoloSMMA(self._p)

        self.tr = ValueFunc('tr')
        self.atr = ValueFunc('atr')

        super().__init__(HIGH_PRIORITY)

    def addData(self, bar: Bar) -> None:
        if self._prevClose is None:
            self._prevClose = bar.close
            return

        self.tr.set(max(bar.hi, self._prevClose) - min(bar.lo, self._prevClose))
        self.atr.set(self._atr_smma.next(self.tr()))

        self._prevClose = bar.close

    def setupTime(self) -> int:
        return self._atr_smma.setupTime() + 1
