from cash_money.nodes.cmNode import CMNode
from nodepasta.node import Port
from nodepasta.argtypes import FLOAT, EnumNodeArg
from nodepasta.errors import ExecutionError, NodeDefError

import operator


class MathNode(CMNode):
    DESCRIPTION = "Calculates basic math operations on two operands.\nA (operation) B"
    _INPUTS = [Port("A", FLOAT, "The first operand"), Port("B", FLOAT, "The second operand")]
    _OUTPUTS = [Port("Out", FLOAT, "The output of the operation")]
    _ARGS = [
        EnumNodeArg(
            "op",
            "Operation",
            "The operation to perform",
            "ADD", ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "MIN", "MAX"]
        )
    ]
    NODETYPE = "Math"

    def init(self):
        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]
        self.op = None

    def setup(self) -> None:
        x = self.args["op"].value

        if x == "ADD":
            self.op = operator.add
        elif x == "SUBTRACT":
            self.op = operator.sub
        elif x == "MULTIPLY":
            self.op = operator.mul
        elif x == "DIVIDE":
            self.op = operator.truediv
        elif x == "MIN":
            self.op = min
        elif x == "MAX":
            self.op = max
        else:
            raise NodeDefError("MathNode.init", f"Unknown operation: {x}")

    def setupTime(self) -> int:
        return 1

    def execute(self) -> None:
        if self.a.value() is None or self.b.value() is None:
            self.out.value(None)
        elif self.op is None:
            raise ExecutionError("MathNode", "Node not setup")
        else:
            self.out.value(self.op(self.a.value(), self.b.value()))
