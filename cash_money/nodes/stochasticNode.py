from collections import deque

from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.stats.sma import SMA

KP = '_KP'
DP = '_DP'
SP = '_SP'


class Stochastic(CMNode):
    DESCRIPTION = "Calculates the Stochastic Oscillator Indicator." \
                  "Calculated as:\n" \
                  "%K = ((C - L)/(H - L)) * 100\n" \
                  "Where:\n" \
                  "\tC: The most recent closing price\n" \
                  '\tL: The lowest price traded in the last "K Period" cycles\n' \
                  '\tH: The highest price traded in the last "K Period" cycles\n' \
                  '\t%K: The current stochastic indicator\n' \
                  '%D is an SMA over %K with period "D Period"\n' \
                  '%D-Slow is an SMA over %D with period "D-Slow Period"'

    _OUTPUTS = [
        OutPort("%K", FLOAT, 'The "fast" stochastic indicator'),
        OutPort("%D", FLOAT, 'The "slow" stochastic indicator'),
        OutPort("%D-Slow", FLOAT, 'The slowest stochastic indicator')
    ]
    _ARGS = [
        NodeArg(KP, INT, 'K Period', "The number of cycles to choose the highest and lowest", 5),
        NodeArg(DP, INT, 'D Period', "The period the %D SMA", 5),
        NodeArg(SP, INT, 'Slow-D Period', "The period of the %D-Slow SMA", 0)
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
