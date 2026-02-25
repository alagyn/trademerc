from nodepasta.argtypes import FLOAT, BOOL
from nodepasta.node import Port

from cash_money.nodes.cmNode import CMNode
from cash_money.stats.crossover import Crossover, CrossoverType


class CrossoverNode(CMNode):
    DESCRIPTION = "Checks if input A crosses input B."
    _INPUTS = [Port("A", FLOAT, "The first input"), Port("B", FLOAT, "The second input")]
    _OUTPUTS = [
        Port("Delta", FLOAT, "Outputs 1 if A crosses up through B, -1 if A crosses down, else 0"),
        Port("Cross Up", BOOL, "True if and only if A crosses up through B"),
        Port("Cross Down", BOOL, "True if and only if A crosses down through B")
    ]
    NODETYPE = "Crossover"

    def init(self):
        self.co = Crossover()

        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.delta = self.outputs[0]
        self.crossUp = self.outputs[1]
        self.crossDn = self.outputs[2]

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        a = self.a.value()
        b = self.b.value()

        if a is None or b is None:
            self.delta.value(None)
            self.crossUp.value(None)
            self.crossDn.value(None)
            return

        out = self.co.check(a, b)

        if out == CrossoverType.CROSS_UP:
            self.delta.value(1)
            self.crossUp.value(True)
            self.crossDn.value(False)
        elif out == CrossoverType.CROSS_DOWN:
            self.delta.value(-1)
            self.crossUp.value(False)
            self.crossDn.value(True)
        else:
            self.delta.value(0)
            self.crossUp.value(False)
            self.crossDn.value(False)

    def setupTime(self) -> int:
        return 2
