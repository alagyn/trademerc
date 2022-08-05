from nodepasta.argtypes import FLOAT
from nodepasta.node import OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode

AF_INC = 0.02

_AF = '_AF'
_AFMAX = '_AFMAX'


class ParabolicSAR(CMNode):
    DESCRIPTION = "Calculates the Parabolic Stop-And-Release (PSAR).\nIt's complicated, google it."
    _OUTPUTS = [
        OutPort("PSAR", FLOAT, "The PSAR")
    ]
    _ARGS = [
        NodeArg(_AF, FLOAT, "AF Start", "The starting AF value", 0.02),
        NodeArg(_AFMAX, FLOAT, "AF Max", "The maximum AF value", 0.2)
    ]
    NODETYPE = "PSAR"

    def __init__(self):
        super().__init__()
        self._afStart = self.args[_AF]
        self._af: float = self._afStart.value
        self._afMax = self.args[_AFMAX]

        self._extreme = None
        self._trend = False

        self._nextSAR = None

        self._prevHigh = None
        self._prevLow = None

        self.out = self.outputs[0]

    def setup(self) -> None:
        self._af: float = self._afStart.value
        self._extreme = None
        self._trend = False

        self._nextSAR = None

        self._prevHigh = None
        self._prevLow = None

    def execute(self) -> None:
        hi, lo, close = self.hlc()

        # Start case, takes 2 iterations to setup
        if self._nextSAR is None:
            if self._prevLow is None:
                self._prevLow = close
                self.out.setValue(None)
                return

            # estimated downtrend
            if self._prevLow < close:
                self._trend = False
                self._extreme = lo
            # else uptrend
            else:
                self._trend = True
                self._extreme = hi

            self._nextSAR = (hi + lo) / 2
            self._prevLow = lo
            self._prevHigh = hi
            self.out.setValue(None)
            return

        # Update to today's SAR
        todayPSAR = self._nextSAR

        # Check for a trend switch
        if (self._trend and todayPSAR >= lo) or (not self._trend and todayPSAR <= hi):
            # Reverse the trend
            self._trend = not self._trend
            todayPSAR = self._extreme
            self._extreme = hi if self._trend else lo
            self._af = self._afStart.value

        # Check for new EP, inc AF if found
        if self._trend:
            if hi > self._extreme:
                self._extreme = hi
                self._af += AF_INC
        else:
            if lo < self._extreme:
                self._extreme = lo
                self._af += AF_INC

        # limit AF to max
        self._af = min(self._af, self._afMax.value)

        # calc tomorrow's psar
        self._nextSAR = todayPSAR + self._af * (self._extreme - todayPSAR)

        # Limit tomorrow's psar using ITS prev 2 lows and highs, i.e today's and yesterday's lows
        if self._trend:
            # uptrend, sar should be below prev 2 lows
            self._nextSAR = min(lo, self._prevLow, self._nextSAR)
        else:
            # downtrend, sar should be above prev 2 highs
            self._nextSAR = max(hi, self._prevHigh, self._nextSAR)

        # update prev vals
        self._prevLow = lo
        self._prevHigh = hi

        self.out.setValue(todayPSAR)

    def setupTime(self) -> int:
        return 2
