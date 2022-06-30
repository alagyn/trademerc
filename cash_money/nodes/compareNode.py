from operator import lt, gt

from nodepasta.argtypes import FLOAT, BOOL, EnumNodeArg
from nodepasta.node import InPort, OutPort

from cash_money.nodes.cmNode import CMNode

_TYPE = '_TYPE'


class Compare(CMNode):
    _INPUTS = [
        InPort("A", FLOAT),
        InPort("B", FLOAT)
    ]
    _OUTPUTS = [
        OutPort("Check", BOOL)
    ]
    _ARGS = [
        EnumNodeArg(_TYPE, "Type", "<", ["<", ">"])
    ]
    NODETYPE = "Compare"

    def __init__(self):
        super().__init__()
        self._opType = self.args[_TYPE]
        self.op = None
        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]

    def setup(self) -> None:
        if self._opType == "<":
            self.op = lt
        else:
            self.op = gt

    def setupTime(self) -> int:
        return 1

    def execute(self) -> None:
        if self.a.value is None or self.b.value is None:
            self.out.setValue(None)
        else:
            self.out.setValue(self.op(self.a.value, self.b.value))
