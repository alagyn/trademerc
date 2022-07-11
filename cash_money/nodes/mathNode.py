from cash_money.nodes.cmNode import CMNode
from nodepasta.node import InPort, OutPort
from nodepasta.argtypes import FLOAT, EnumNodeArg
from nodepasta.errors import ExecutionError

import operator

class MathNode(CMNode):
    _INPUTS = [
        InPort("A", FLOAT),
        InPort("B", FLOAT)
    ]
    _OUTPUTS = [
        OutPort("Out", FLOAT)
    ]
    _ARGS = [
        EnumNodeArg("op", "Operation", "+", ["+", "-", "*", "/"])
    ]
    NODETYPE = "Math"

    def __init__(self):
        super(MathNode, self).__init__()
        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]
        self.op = None

    def setup(self) -> None:
        x = self.args["op"].value

        if x == "+":
            self.op = operator.add
        elif x == "-":
            self.op = operator.sub
        elif x == "*":
            self.op = operator.mul
        elif x == "/":
            self.op = operator.truediv

    def setupTime(self) -> int:
        return 1

    def execute(self) -> None:
        if self.a.value is None or self.b.value is None:
            self.out.setValue(None)
        elif self.op is None:
            raise ExecutionError("MathNode", "Node not setup")
        else:
            self.out.setValue(self.op(self.a.value, self.b.value))
