from indicators.indicator import Indicator, HIGH_PRIORITY, ValueFunc
from indicators.sma import SoloSMA
from collections import deque


class Stochastic(Indicator):
    def __init__(self, kPeriod: int, dPeriod: int, slowPeriod: int = 0):
        """
        Stochastic Oscillator Indicator
        :param kPeriod: The period of the percK calculations
        :param dPeriod: The period of the percD SMA calculations
        :param slowPeriod: If > 0, adds another SMA with the given period
        """
        super().__init__(HIGH_PRIORITY)

        self._kp = kPeriod
        self._dp = dPeriod
        self._sp = slowPeriod
        self.slow = self._sp > 0

        self._percK = 0

        self._percD = 0
        self._percDfast = SoloSMA(dPeriod)
        self._percDslow = SoloSMA(slowPeriod)

        self.lows = deque()
        self.highs = deque()

    def addData(self, low, close, high) -> None:
        self.lows.append(low)
        self.highs.append(high)
        if len(self.lows) > self._kp:
            self.lows.popleft()
            self.highs.popleft()

        lowest = min(self.lows)
        highest = max(self.highs)

        self._percK = 100 * (close - lowest) / (highest - lowest)
        self._percD = self._percDfast.next(self._percK)

        if self.slow:
            self._percD = self._percDslow.next(self._percD)


    @ValueFunc(key='percentK')
    def percK(self) -> float:
        return self._percK

    @ValueFunc(key='percentD')
    def percD(self) -> float:
        return self._percD

    def setupTime(self) -> int:
        return self._kp + self._dp + self._sp