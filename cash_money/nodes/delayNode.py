from collections import deque

from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import InPort, OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode

_D = '_D'

class DelayNode(CMNode):
    _INPUTS = [
        InPort("In", FLOAT)
    ]
    _OUTPUTS = [
        OutPort("Out", FLOAT)
    ]
    _ARGS = [
        NodeArg(_D, INT, "Delay", 1)
    ]
    NODETYPE = "Delay"

    def __init__(self):
        super().__init__()
        self._d = self.args[_D]
        self._q = deque()
        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        self._q.clear()

    def setupTime(self) -> int:
        return self._d.value

    def execute(self) -> None:
        self._q.append(self.a.value)
        if len(self._q) > self._d.value:
            self.out.setValue(self._q.popleft())
        else:
            self.out.setValue(None)
