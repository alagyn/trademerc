from cash_money.indicators.indicator import Indicator
from cash_money.objects.strategy_params import DataSelector, NumberParam
from collections import deque
from cash_money.indicators.lineManager import LineManager, Data


class SoloSMA:
    def __init__(self, period: int):
        self.avg = 0
        self.vals = deque()
        self.p = period

    def next(self, data) -> float:
        self.vals.append(data)
        if len(self.vals) <= self.p:
            self.avg = sum(self.vals) / len(self.vals)
        else:
            old = self.vals.popleft()
            self.avg = self.avg + (data - old) / self.p

        return self.avg

    def getValue(self) -> float:
        return self.avg


_SMA = 'SMA'


class SMA(Indicator):
    """
    Simple Moving Average
    """

    params = [NumberParam('period', "Period", int, 5),
              DataSelector()]
    outputs = [_SMA]

    def __init__(self, name: str, lineManager: LineManager, period: int, data: Data):
        super().__init__(name)
        self.avg = lineManager.registerLine(name, _SMA)
        self._data = data.requestLine(name, lineManager)
        self._sma = SoloSMA(period)
        self._p = period

    def update(self) -> None:
        out = self._sma.next(self._data())
        self.avg.add(out)

    def setupTime(self) -> int:
        return self._p
