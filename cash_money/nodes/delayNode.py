from collections import deque

from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import Port, NodeArg

from cash_money.nodes.cmNode import CMNode

_D = '_D'


class DelayNode(CMNode):
    DESCRIPTION = "Inputs are stored and then output at a specific delay"
    _INPUTS = [
        Port("In", FLOAT, "The input value")
    ]
    _OUTPUTS = [
        Port("Out", FLOAT, "The output value")
    ]
    _ARGS = [
        NodeArg(_D, INT, "Delay", "The number of cycles to delay outputs", 1)
    ]
    NODETYPE = "Delay"

    def init(self):
        self._d = self.args[_D]
        self._q = deque()
        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        self._q.clear()

    def setupTime(self) -> int:
        return self._d.value

    def execute(self) -> None:
        self._q.append(self.a.value())
        if len(self._q) > self._d.value:
            self.out.value(self._q.popleft())
        else:
            self.out.value(None)
