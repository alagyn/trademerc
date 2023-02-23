from operator import lt, gt

from nodepasta.argtypes import FLOAT, BOOL, EnumNodeArg
from nodepasta.node import Port

from cash_money.nodes.cmNode import CMNode

_TYPE = '_TYPE'


class Compare(CMNode):
    DESCRIPTION = "Ouputs the comparison of two numbers.\nA (operation) B"
    _INPUTS = [
        Port("A", FLOAT, "The first operand"),
        Port("B", FLOAT, "The second operand")
    ]
    _OUTPUTS = [
        Port("Check", BOOL, "The boolean output (true/false)")
    ]
    _ARGS = [
        EnumNodeArg(_TYPE, "Type", "The operation to perform",
                    "LESS THAN", ["LESS THAN", "GREATER THAN"])
    ]
    NODETYPE = "Compare"

    def init(self):
        self._opType = self.args[_TYPE]
        self.op = lt
        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]

    def setup(self) -> None:
        if self._opType == "LESS THAN":
            self.op = lt
        else:
            self.op = gt

    def setupTime(self) -> int:
        return 1

    def execute(self) -> None:
        if self.a.value() is None or self.b.value() is None:
            self.out.value(None)
        else:
            self.out.value(self.op(self.a.value(), self.b.value()))
