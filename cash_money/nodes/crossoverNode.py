from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import InPort, OutPort

from cash_money.nodes.cmNode import CMNode


class Crossover(CMNode):
    _INPUTS = [
        InPort("A", FLOAT),
        InPort("B", FLOAT)
    ]
    _OUTPUTS = [
        OutPort("Delta", INT)
    ]
    NODETYPE = "Crossover"

    def __init__(self):
        super().__init__()
        self.prevDiff = None
        self.curDiff = None

        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]

    def setup(self) -> None:
        self.prevDiff = None
        self.curDiff = None

    def execute(self) -> None:
        if self.a.value is None or self.b.value is None:
            self.out.setValue(None)

        if self.curDiff is None:
            self.curDiff = self.a.value - self.b.value
            self.out.setValue(0)

        self.prevDiff = self.curDiff
        self.curDiff = self.a.value - self.b.value

        # Upcross
        if self.prevDiff < 0 < self.curDiff:
            self.out.setValue(1)
        # Downcross
        elif self.prevDiff > 0 > self.curDiff:
            self.out.setValue(-1)
        else:
            self.out.setValue(0)

    def setupTime(self) -> int:
        return 2
