from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import InPort, OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.stats.sma import SMA

_P = "_p"


class SMANode(CMNode):
    """
    Simple Moving Average
    """

    _INPUTS = [
        InPort("Value", FLOAT)
    ]
    _OUTPUTS = [
        OutPort("SMA", FLOAT)
    ]
    _ARGS = [
        NodeArg(_P, INT, "Period", 5)
    ]
    NODETYPE = "Simple Moving Avg"

    def __init__(self):
        super().__init__()

        self._p = self.args[_P]
        self._sma = None

        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        self._sma = SMA(self._p.value)

    def execute(self) -> None:
        if self.a.value is None:
            self.out.setValue(None)
        else:
            self.out.setValue(self._sma.next(self.a.value))

    def setupTime(self) -> int:
        return self._p.value
