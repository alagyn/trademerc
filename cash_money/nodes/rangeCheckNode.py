from nodepasta.argtypes import FLOAT, BOOL
from nodepasta.node import Port, NodeArg

from cash_money.nodes.cmNode import CMNode

_MIN = '_min'
_MAX = '_max'


class RangeCheck(CMNode):
    DESCRIPTION = "Checks if the input is within a set range"
    _INPUTS = [
        Port("Value", FLOAT, "The input")
    ]
    _OUTPUTS = [
        Port("Check", BOOL, "Outputs true if and only if the input is greater than the min and less than the max")
    ]
    # TODO change to be a port
    _ARGS = [
        NodeArg(_MIN, FLOAT, "Min", "The minimum value", 0),
        NodeArg(_MAX, FLOAT, "Max", "The maximum value", 1.0)
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
        if self.a.value() is None:
            self.out.value(None)
        else:
            self.out.value(self.minVal.value <= self.a.value() <= self.maxVal.value)
