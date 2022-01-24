from indicators.indicator import Indicator, ValueFunc, NumberParam
from indicators.indicatorManager import HIGH_PRIORITY
from indicators.sma import SoloSMA
from collections import deque

_PERCK = 'Percent K'
_PERCD = 'Percent D'
_PERCDSLOW = 'Percent D slow'


class Stochastic(Indicator):
    params = {'kPeriod': NumberParam(int, 5),
              'dPeriod': NumberParam(int, 5),
              'slowPeriod': NumberParam(int, 0)}
    outputs = [_PERCK, _PERCD, _PERCDSLOW]

    def __init__(self, kPeriod: int, dPeriod: int, slowPeriod: int = 0):
        """
        Stochastic Oscillator Indicator
        :param kPeriod: The period of the percK calculations
        :param dPeriod: The period of the percD SMA calculations
        :param slowPeriod: If > 0, adds another SMA with the given period
        """

        self._kp = kPeriod
        self._dp = dPeriod
        self._sp = slowPeriod
        self.slow = self._sp > 0

        self.percK = ValueFunc(_PERCK)
        self.percDFast = ValueFunc(_PERCD)
        self.percDSlow = ValueFunc(_PERCDSLOW)

        self._percDfast = SoloSMA(dPeriod)
        self._percDslow = SoloSMA(slowPeriod)

        self.lows = deque()
        self.highs = deque()

        super().__init__(HIGH_PRIORITY)

    def addData(self, low, close, high) -> None:
        self.lows.append(low)
        self.highs.append(high)
        if len(self.lows) > self._kp:
            self.lows.popleft()
            self.highs.popleft()

        lowest = min(self.lows)
        highest = max(self.highs)

        newPercK = 100 * (close - lowest) / (highest - lowest)
        self.percK.set(newPercK)

        newPerD = self._percDfast.next(newPercK)
        self.percDFast.set(newPerD)

        if self.slow:
            newPerDSlow = self._percDslow.next(newPerD)
            self.percDSlow.set(newPerDSlow)




    def setupTime(self) -> int:
        return self._kp + self._dp + self._sp
