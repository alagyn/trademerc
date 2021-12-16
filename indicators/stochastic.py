from indicators.indicator import Indicator, HIGH_PRIORITY
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

    def addData(self, *, low=None, close=None, high=None) -> None:
        self.lows.append(low)
        self.highs.append(high)
        if len(self.lows) > self._kp:
            self.lows.popleft()
            self.highs.popleft()

        low = min(self.lows)
        high = max(self.highs)

        self._percK = 100 * (close - low) / (high - low)
        self._percDfast.next(self.percK)

        if self.slow:
            self._percD = self._percDslow.next(self._percDfast.getValue())
        else:
            self._percD = self._percDfast.getValue()

    def percK(self) -> float:
        return self._percK

    def percD(self) -> float:
        return self._percD

    def setupTime(self) -> int:
        return self._kp + self._dp + self._sp