from nodepasta.argtypes import FLOAT
from nodepasta.node import Port

from cash_money.nodes.cmNode import CMNode
from cash_money.stats.smma import SMMA


class AbsoluteValueNode(CMNode):
    DESCRIPTION = "Calculates the Absolute Value"
    _INPUTS = [
        Port("Value", FLOAT, "The input value")
    ]
    _OUTPUTS = [
        Port("ABS", FLOAT, "The Absolute Value")
    ]
    NODETYPE = "Absolute Value"

    def __init__(self):
        super().__init__()
        self.val = self.inputs[0]
        self.absOut = self.outputs[0]

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        val = self.val.value()
        self.absOut.value(abs(val))

    def setupTime(self) -> int:
        return 0
