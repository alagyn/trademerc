from nodepasta.argtypes import FLOAT, BOOL
from nodepasta.node import InPort, OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode

_MAX = '_max'

class MaxCheck(CMNode):
    _INPUTS = [
        InPort("Value", FLOAT)
    ]
    _OUTPUTS = [
        OutPort("Check", BOOL)
    ]
    # TODO change to be a port?
    _ARGS = [
        NodeArg(_MAX, FLOAT, "Max", 1.0)
    ]
    NODETYPE = "Max"

    def __init__(self):
        super().__init__()
        self._max = self.args[_MAX]

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
            self.out.setValue(self.a < self._max)
