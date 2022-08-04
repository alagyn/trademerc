from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import InPort, OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.stats.ema import EMA

_P = "_period"
_S = "_smooth"

class EMANode(CMNode):
    """
    Exponential Moving Average
    """
    DESCRIPTION = "Calculates the Exponential Moving Average"
    _INPUTS = [
        InPort("Value", FLOAT, "The input value")
    ]
    _OUTPUTS = [
        OutPort("EMA", FLOAT, "The averaged value")
    ]
    _ARGS = [
        NodeArg(_P, INT, "Period", "The period of the moving average", 5),
        NodeArg(_S, FLOAT, "Smoothing", "The smoothing factor", 2.0)
    ]
    NODETYPE = "Exponential Moving Avg"

    def __init__(self, ):
        super().__init__()

        self._ema = None
        self._s = self.args[_S]
        self._p = self.args[_P]

        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        self._ema = EMA(smoothing=self._s.value, period=self._p.value)

    def execute(self) -> None:
        if self.a.value is None:
            self.out.setValue(None)
        else:
            self.out.setValue(self._ema.next(self.a.value))

    def setupTime(self) -> int:
        return self._p.value
