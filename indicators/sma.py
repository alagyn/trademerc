from indicators.indicator import Indicator, HIGH_PRIORITY, ValueFunc
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



class SMA(Indicator):
    """
    Simple Moving Average
    """


    def __init__(self, period: int, data='c'):
        super().__init__(HIGH_PRIORITY)
        self.avg = 0
        self.data = data
        self.sma = SoloSMA(period)
        self._p = period

    def addData(self, *, low=None, close=None, high=None) -> None:
        if self.data == 'c':
            self.avg = self.sma.next(close)
        elif self.data == 'l':
            self.avg = self.sma.next(low)
        else:
            self.avg = self.sma.next(high)

    @ValueFunc(key='sma')
    def getValue(self) -> float:
        return self.avg

    def setupTime(self) -> int:
        return self._p
