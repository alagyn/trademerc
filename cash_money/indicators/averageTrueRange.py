from cash_money.indicators.indicator import Indicator
from cash_money.indicators.lineManager import LineManager, CLOSE, HIGH, LOW
from cash_money.objects.strategy_params import NumberParam
from cash_money.indicators.smma import SoloSMMA


class AverageTrueRange(Indicator):
    params = [NumberParam("period", "Period", int, 5)]
    outputs = ['tr', 'atr']

    def __init__(self, name: str, lineManager: LineManager, period: int):
        super().__init__(name)
        self._p = period

        self._prevClose = None
        self._atr_smma = SoloSMMA(self._p)

        self.tr = lineManager.registerLine(name, 'tr')
        self.atr = lineManager.registerLine(name, 'atr')

        self.close = lineManager.requestInput(CLOSE)
        self.hi = lineManager.requestInput(HIGH)
        self.lo = lineManager.requestInput(LOW)

    def update(self) -> None:
        if self._prevClose is None:
            self._prevClose = self.close()
            return

        self.tr.add(max(self.hi(), self._prevClose) - min(self.lo(), self._prevClose))
        self.atr.add(self._atr_smma.next(self.tr()))

        self._prevClose = self.close()

    def setupTime(self) -> int:
        return self._atr_smma.setupTime() + 1
