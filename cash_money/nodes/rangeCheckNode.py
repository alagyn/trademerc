from nodepasta.argtypes import FLOAT, BOOL
from nodepasta.node import InPort, OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode

_MIN = '_min'
_MAX = '_max'


class RangeCheck(CMNode):
    _INPUTS = [
        InPort("Value", FLOAT)
    ]
    _OUTPUTS = [
        OutPort("Check", BOOL)
    ]
    # TODO change to be a port
    _ARGS = [
        NodeArg(_MIN, FLOAT, "Min", 0),
        NodeArg(_MAX, FLOAT, "Max", 1.0)
    ]
    NODETYPE = "Range"

    def __init__(self):
        super().__init__()
        self.minVal = self.args[_MIN]
        self.maxVal = self.args[_MAX]

        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        pass

    def setupTime(self) -> int:
        return 0

    def execute(self) -> None:
        if self.a.value is None:
            self.out.setValue(None)
        else:
            self.out.setValue(self.minVal.value <= self.a.value <= self.maxVal.value)
