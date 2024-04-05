from nodepasta.argtypes import BOOL, EnumNodeArg
from nodepasta.node import Port
from nodepasta.errors import NodeDefError

from cash_money.nodes.cmNode import CMNode

from operator import or_, and_, xor

_OP = "_OP"


class LogicNode(CMNode):
    DESCRIPTION = ("Boolean Logic Operations\n"
                   "Performs A (operation) B")
    _INPUTS = [Port("A", BOOL, "Input A"), Port("B", BOOL, "Input B")]
    _OUTPUTS = [Port("Result", BOOL, "Output of operation")]
    _ARGS = [EnumNodeArg(_OP, "Type", "The operation to perform", "OR", ["OR", "AND", "XOR"])]
    NODETYPE = "Logic"

    def init(self) -> None:
        self._opType = self.args[_OP]
        self.op = or_
        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]

    def setup(self) -> None:
        if self._opType.value == "OR":
            self.op = or_
        elif self._opType.value == "AND":
            self.op = and_
        elif self._opType.value == "XOR":
            self.op = xor
        else:
            raise NodeDefError("logicNode.setup()", f"Invalid option '{self._opType.value}'")
