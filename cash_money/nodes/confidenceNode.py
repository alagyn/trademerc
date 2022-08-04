from cash_money.nodes.cmNode import CMNode

from nodepasta.node import InPort, OutPort, NodeArg
from nodepasta.argtypes import BOOL, FLOAT

_EnterThresh = "enterThresh"
_ExitThresh = "exitThresh"

class ConfidenceNode(CMNode):
    DESCRIPTION = "Takes in a variable number of weights and sums them, then compares against a threshold.\n" \
                  "Inputs do not have to sum to 1"
    _INPUTS = [
        InPort("Weights", FLOAT, "The input weights",
               variable=True, cnt=1)
    ]
    _OUTPUTS = [
        OutPort("Enter", BOOL, 'Outputs "true" if and only if the sum is greater than the enter threshold'),
        OutPort("Exit", BOOL, 'Outputs "true" if and only if the sum is less than the exit threshold')
    ]
    _ARGS = [
        NodeArg(_EnterThresh, FLOAT, "Enter Threshold", "The entry theshold", 0.5),
        NodeArg(_ExitThresh, FLOAT, "Exit Threshold", "The exit threshold", 0.5)
    ]
    NODETYPE = "Confidence"

    def __init__(self):
        super(ConfidenceNode, self).__init__()

        self.enterThresh = self.args[_EnterThresh]
        self.exitThresh = self.args[_ExitThresh]

        self.weights = self.inputs[0]

        self.enter = self.outputs[0]
        self.exit = self.outputs[1]

    def setup(self) -> None:
        pass

    def setupTime(self) -> int:
        return 1

    def execute(self) -> None:
        self.enter.setValue(False)
        self.exit.setValue(False)

        if self.weights.value is None:
            return

        value = sum(self.weights.value)
        if value >= self.enterThresh.value:
            self.enter.setValue(True)
        if value <= self.exitThresh.value:
            self.exit.setValue(True)
