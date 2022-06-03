from cash_money.indicators.indicator import Indicator
from cash_money.objects.strategy_params import NumberParam
from cash_money.indicators.sma import SoloSMA
from .lineManager import LineManager
from collections import deque

_PERCK = 'Percent K'
_PERCD = 'Percent D'
_PERCDSLOW = 'Percent D slow'


class Stochastic(Indicator):
    params = [NumberParam('kPeriod', "K Period", int, 5),
              NumberParam('dPeriod', "D Period", int, 5),
              NumberParam('slowPeriod', "Slow-D Period", int, 0)]
    outputs = [_PERCK, _PERCD, _PERCDSLOW]

    def __init__(self, name: str, lineManager: LineManager, kPeriod: int, dPeriod: int, slowPeriod: int = 0):
        """
        Stochastic Oscillator Indicator
        :param kPeriod: The period of the percK calculations
        :param dPeriod: The period of the percD SMA calculations
        :param slowPeriod: If > 0, adds another SMA with the given period
        """
        super().__init__(name)

        self._kp = kPeriod
        self._dp = dPeriod
        self._sp = slowPeriod
        self.slow = self._sp > 0

        self.percK = lineManager.registerLine(name, _PERCK)
        self.percDFast = lineManager.registerLine(name, _PERCD)
        self.percDSlow = lineManager.registerLine(name, _PERCDSLOW)

        self._percDfast = SoloSMA(dPeriod)
        self._percDslow = SoloSMA(slowPeriod)

        self.lows = deque()
        self.highs = deque()

        self.hi, self.lo, self.close = lineManager.hlc()


    def update(self) -> None:
        self.lows.append(self.lo())
        self.highs.append(self.hi())
        if len(self.lows) > self._kp:
            self.lows.popleft()
            self.highs.popleft()

        lowest = min(self.lows)
        highest = max(self.highs)

        newPercK = 100 * (self.close() - lowest) / (highest - lowest)
        self.percK.add(newPercK)

        newPerD = self._percDfast.next(newPercK)
        self.percDFast.add(newPerD)

        if self.slow:
            newPerDSlow = self._percDslow.next(newPerD)
            self.percDSlow.add(newPerDSlow)




    def setupTime(self) -> int:
        return self._kp + self._dp + self._sp
