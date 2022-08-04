from nodepasta.argtypes import FLOAT, BOOL
from nodepasta.node import InPort, OutPort

from cash_money.nodes.cmNode import CMNode


class Crossover(CMNode):
    DESCRIPTION = "Checks if input A crosses input B."
    _INPUTS = [
        InPort("A", FLOAT, "The first input"),
        InPort("B", FLOAT, "The second input")
    ]
    _OUTPUTS = [
        OutPort("Delta", FLOAT, "Outputs 1 if A crosses up through B, -1 if A crosses down, else 0"),
        OutPort("Cross Up", BOOL, "True if and only if A crosses up through B"),
        OutPort("Cross Down", BOOL, "True if and only if A crosses down through B")
    ]
    NODETYPE = "Crossover"

    def __init__(self):
        super().__init__()
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
        if self.a.value is None or self.b.value is None:
            self.delta.setValue(None)
            self.crossUp.setValue(None)
            self.crossDn.setValue(None)

        if self.curDiff is None:
            self.curDiff = self.a.value - self.b.value
            self.delta.setValue(0)
            self.crossDn.setValue(False)
            self.crossUp.setValue(True)
            return

        self.prevDiff = self.curDiff
        self.curDiff = self.a.value - self.b.value

        # Upcross
        if self.prevDiff < 0 < self.curDiff:
            self.delta.setValue(1)
            self.crossUp.setValue(True)
            self.crossDn.setValue(False)
        # Downcross
        elif self.prevDiff > 0 > self.curDiff:
            self.delta.setValue(-1)
            self.crossUp.setValue(False)
            self.crossDn.setValue(True)
        else:
            self.delta.setValue(0)
            self.crossUp.setValue(False)
            self.crossDn.setValue(False)

    def setupTime(self) -> int:
        return 2
