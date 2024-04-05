from nodepasta.argtypes import FLOAT, BOOL
from nodepasta.node import Port

from cash_money.nodes.cmNode import CMNode


class Crossover(CMNode):
    DESCRIPTION = "Checks if input A crosses input B."
    _INPUTS = [Port("A", FLOAT, "The first input"), Port("B", FLOAT, "The second input")]
    _OUTPUTS = [
        Port("Delta", FLOAT, "Outputs 1 if A crosses up through B, -1 if A crosses down, else 0"),
        Port("Cross Up", BOOL, "True if and only if A crosses up through B"),
        Port("Cross Down", BOOL, "True if and only if A crosses down through B")
    ]
    NODETYPE = "Crossover"

    def init(self):
        self.prevDiff = None
        self.curDiff = None

        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.delta = self.outputs[0]
        self.crossUp = self.outputs[1]
        self.crossDn = self.outputs[2]

    def setup(self) -> None:
        self.prevDiff = None
        self.curDiff = None

    def execute(self) -> None:
        if self.a.value() is None or self.b.value() is None:
            self.delta.value(None)
            self.crossUp.value(None)
            self.crossDn.value(None)

        if self.curDiff is None:
            self.curDiff = self.a.value() - self.b.value()
            self.delta.value(0)
            self.crossDn.value(False)
            self.crossUp.value(True)
            return

        self.prevDiff = self.curDiff
        self.curDiff = self.a.value() - self.b.value()

        # Upcross
        if self.prevDiff < 0 < self.curDiff:
            self.delta.value(1)
            self.crossUp.value(True)
            self.crossDn.value(False)
        # Downcross
        elif self.prevDiff > 0 > self.curDiff:
            self.delta.value(-1)
            self.crossUp.value(False)
            self.crossDn.value(True)
        else:
            self.delta.value(0)
            self.crossUp.value(False)
            self.crossDn.value(False)

    def setupTime(self) -> int:
        return 2
