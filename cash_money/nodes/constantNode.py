from nodepasta.argtypes import FLOAT
from nodepasta.node import OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode

class ConstantNode(CMNode):
    DESCRIPTION = "Outputs a constant value"
    _INPUTS = []
    _OUTPUTS = [
        OutPort("Value", FLOAT, "The value")
    ]
    _ARGS = [
        NodeArg("value", FLOAT, "Value", "The value", 1)
    ]
    NODETYPE = 'Constant'

    def __init__(self):
        super(ConstantNode, self).__init__()
        self.out = self.outputs[0]
        self.val = self.args['value']

    def setup(self) -> None:
        pass

    def setupTime(self) -> int:
        return 0

    def execute(self) -> None:
        self.out.setValue(self.val.value)
