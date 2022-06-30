from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.nodes.datakeys import HIGH, LOW, CLOSE
from cash_money.stats.smma import SMMA

PERIOD = 'period'


class AverageTrueRange(CMNode):
    _INPUTS = []
    _OUTPUTS = [OutPort("ATR", FLOAT), OutPort("TR", FLOAT)]
    _ARGS = [NodeArg(PERIOD, INT, "Period", 5)]
    NODETYPE = "Average True Range"

    def __init__(self):
        super().__init__()
        self._p = self.args[PERIOD]

        self._prevClose = None
        self._atr_smma = None

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
            self.atrOut.setValue(None)
            self.trOut.setValue(None)
            return

        tr = max(hi, self._prevClose) - min(lo, self._prevClose)
        atr = self._atr_smma.next(tr)

        self._prevClose = close

        self.atrOut.setValue(atr)
        self.trOut.setValue(tr)

    def setupTime(self) -> int:
        return self._atr_smma.setupTime() + 1
