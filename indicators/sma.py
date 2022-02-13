from indicators.indicator import Indicator, ValueFunc
from objects.strategy_params import DataSelector, NumberParam
from indicators.indicatorManager import HIGH_PRIORITY
from collections import deque


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

    def __init__(self, period: int, data='c'):
        self.avg = ValueFunc(_SMA)
        self._data = data
        self._sma = SoloSMA(period)
        self._p = period

        super().__init__(HIGH_PRIORITY)

    def addData(self, low, close, high) -> None:
        if self._data == 'c':
            out = self._sma.next(close)
        elif self._data == 'l':
            out = self._sma.next(low)
        else:
            out = self._sma.next(high)

        self.avg.set(out)

    def setupTime(self) -> int:
        return self._p
