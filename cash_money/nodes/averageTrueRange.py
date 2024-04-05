from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import Port, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.nodes.datakeys import HIGH, LOW, CLOSE
from cash_money.stats.smma import SMMA

from typing import Optional

PERIOD = 'period'


class AverageTrueRange(CMNode):
    DESCRIPTION = "Calculates the True Range, which is calculated as:\n" \
                  "max(close, high) - min(close, low)\n" \
                  "The average true range is the true range input into a smoothed moving average"
    _INPUTS = []
    _OUTPUTS = [Port("ATR", FLOAT, "The Average True Range"), Port("TR", FLOAT, "The True Range")]
    _ARGS = [NodeArg(PERIOD, INT, "Period", "The period of the ATR moving average", 5)]
    NODETYPE = "Average True Range"

    def init(self):
        self._p = self.args[PERIOD]

        self._prevClose: Optional[float] = None
        self._atr_smma = SMMA(self._p.value)

        self.atrOut = self.outputs[0]
        self.trOut = self.outputs[1]

    def setup(self) -> None:
        self._prevClose = None
        self._atr_smma = SMMA(self._p.value)

    def execute(self) -> None:
        lo = self.datamap[LOW]
        close = self.datamap[CLOSE]
        hi = self.datamap[HIGH]

        if self._prevClose is None:
            self._prevClose = close
            self.atrOut.value(None)
            self.trOut.value(None)
            return

        tr = max(hi, self._prevClose) - min(lo, self._prevClose)
        atr = self._atr_smma.next(tr)

        self._prevClose = close

        self.atrOut.value(atr)
        self.trOut.value(tr)

    def setupTime(self) -> int:
        return self._atr_smma.setupTime() + 1
