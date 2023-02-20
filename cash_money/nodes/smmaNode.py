from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import Port, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.stats.smma import SMMA

_P = '_p'


class SMMANode(CMNode):
    """Smoothing Moving Average"""

    DESCRIPTION = "Calculates a Smoothing Moving Average (SMMA)"
    _INPUTS = [
        Port("Value", FLOAT, "The input value")
    ]
    _OUTPUTS = [
        Port("SMMA", FLOAT, "The averaged value")
    ]
    _ARGS = [
        NodeArg(_P, INT, "Period", "The period of the moving average", 5)
    ]
    NODETYPE = "Smoothing Moving Avg"

    def __init__(self):
        super().__init__()

        self._p = self.args[_P]
        self._smma = SMMA(self._p.value)

        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        self._smma = SMMA(self._p.value)

    def execute(self) -> None:
        if self.a.value() is None:
            self.out.value(None)
        else:
            self.out.value(self._smma.next(self.a.value()))

    def setupTime(self) -> int:
        return self._smma.setupTime()
