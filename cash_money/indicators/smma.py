from cash_money.indicators.indicator import Indicator
from cash_money.objects.strategy_params import DataSelector, NumberParam
from cash_money.indicators.ema import SoloEMA
from .lineManager import LineManager, Data


class SoloSMMA:
    """
    SMMA is equivalent to an EMA with alpha = 1/period
    """

    def __init__(self, period: int):
        self._a = 1 / period
        self._ema = SoloEMA(alpha=self._a)
        self._p = period

    def next(self, data) -> float:
        return self._ema.next(data)

    def getValue(self) -> float:
        return self._ema.getValue()

    def setupTime(self) -> int:
        return self._p


_SMMA = 'SMMA'


class SMMA(Indicator):
    """Smoothing Moving Average"""

    params = [NumberParam('period', "Period", int, 5),
              DataSelector()]
    outputs = [_SMMA]

    def __init__(self, name: str, lineManager: LineManager, period: int, data: Data):
        super().__init__(name)
        self._data = data.requestLine(name, lineManager)
        self._smma = SoloSMMA(period)
        self.avg = lineManager.registerLine(name, _SMMA)

    def update(self) -> None:
        self.avg.add(self._smma.next(self._data()))

    def setupTime(self) -> int:
        return self._smma.setupTime()
