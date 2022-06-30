from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import InPort, OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.stats.smma import SMMA

_P = '_p'


class SMMANode(CMNode):
    """Smoothing Moving Average"""

    _INPUTS = [
        InPort("Value", FLOAT)
    ]
    _OUTPUTS = [
        OutPort("SMMA", FLOAT)
    ]
    _ARGS = [
        NodeArg(_P, INT, "Period", 5)
    ]
    NODETYPE = "Smoothing Moving Avg"

    def __init__(self):
        super().__init__()

        self._p = self.args[_P]
        self._smma = None

        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        self._smma = SMMA(self._p.value)

    def execute(self) -> None:
        if self.a.value is None:
            self.out.setValue(None)
        else:
            self.out.setValue(self._smma.next(self.a.value))

    def setupTime(self) -> int:
        return self._smma.setupTime()
