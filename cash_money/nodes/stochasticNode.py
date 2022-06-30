from collections import deque

from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.stats.sma import SMA

KP = '_KP'
DP = '_DP'
SP = '_SP'


class Stochastic(CMNode):
    _OUTPUTS = [
        OutPort("%K", FLOAT),
        OutPort("%D", FLOAT),
        OutPort("%D Slow", FLOAT)
    ]
    _ARGS = [
        NodeArg(KP, 'K Period', INT, 5),
        NodeArg(DP, INT, 'D Period', 5),
        NodeArg(SP, INT, 'Slow-D Period', 0)
    ]
    NODETYPE = "Stochastic"

    def __init__(self):
        """
        Stochastic Oscillator Indicator
        """
        super().__init__()

        self._kp = self.args[KP]
        self._dp = self.args[DP]
        self._sp = self.args[SP]
        self.slow = False

        self._percDfast = None
        self._percDslow = None

        self.lows = None
        self.highs = None

        self.percKOut = self.outputs[0]
        self.percDOut = self.outputs[1]
        self.percDSOut = self.outputs[2]

    def setup(self) -> None:
        self.slow = self._sp.value > 0

        self._percDfast = SMA(self._dp.value)
        self._percDslow = SMA(self._sp.value)

        self.lows = deque(maxlen=self._kp.value)
        self.highs = deque(maxlen=self._kp.value)


    def execute(self) -> None:
        hi, lo, close = self.hlc()
        self.lows.append(lo)
        self.highs.append(hi)

        lowest = min(self.lows)
        highest = max(self.highs)

        newPercK = 100 * (close - lowest) / (highest - lowest)
        newPerD = self._percDfast.next(newPercK)

        newPerDSlow = None
        if self.slow:
            newPerDSlow = self._percDslow.next(newPerD)

        self.percKOut.setValue(newPercK)
        self.percDOut.setValue(newPerD)
        self.percDSOut.setValue(newPerDSlow)

    def setupTime(self) -> int:
        return self._kp.value + self._dp.value + self._sp.value
