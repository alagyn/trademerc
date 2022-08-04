from nodepasta.argtypes import BOOL, NodeArg, FLOAT
from nodepasta.node import InPort, OutPort

from cash_money.nodes.cmNode import CMNode

_T = '_type'
_W = '_wgt'

class WeightNode(CMNode):
    DESCRIPTION = "Takes in a boolean (true/false) and outputs a constant value, or zero"
    _INPUTS = [
        InPort("Condition", BOOL, "The boolean condition")
    ]
    _OUTPUTS = [
        OutPort("Value", FLOAT, 'Outputs zero if input is false, else outputs the value of "Weight"')
    ]
    _ARGS = [
        NodeArg(_W, FLOAT, "Weight", "The value to output when the condition is true")
    ]

    NODETYPE = "Weight"

    def __init__(self):
        super(WeightNode, self).__init__()
        self._wgt = self.args[_W]
        self.c = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        pass

    def setupTime(self) -> int:
        return 0

    def execute(self) -> None:
        if self.c.value is None:
            self.out.setValue(None)
        else:
            self.out.setValue(self._wgt.value if self.c.value else 0)
