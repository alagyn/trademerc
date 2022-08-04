from nodepasta.node import InPort, OutPort
from nodepasta.argtypes import BOOL

from cash_money.nodes.cmNode import CMNode

class InvertNode(CMNode):
    DESCRIPTION = "Inverts a boolean (true/false) value."
    _INPUTS = [
        InPort("In", BOOL, "The input")
    ]
    _OUTPUTS = [
        OutPort("Out", BOOL, "The inverse")
    ]
    NODETYPE = "Invert"

    def __init__(self):
        super(InvertNode, self).__init__()
        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setupTime(self) -> int:
        return 1

    def execute(self) -> None:
        if self.a.value is None:
            self.out.setValue(None)
        else:
            self.out.setValue(not self.a.value)

    def setup(self) -> None:
        pass
