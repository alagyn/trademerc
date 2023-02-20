from cash_money.nodes.cmNode import CMNode

from nodepasta.node import Port, NodeArg
from nodepasta.argtypes import BOOL, FLOAT

from cash_money.utils.log_utils import CMLogger
from .datakeys import SYMBOL, DRY_RUN

log = CMLogger("Conf Node")

_EnterThresh = "enterThresh"
_ExitThresh = "exitThresh"


class ConfidenceNode(CMNode):
    DESCRIPTION = "Takes in a variable number of weights and sums them, then compares against a threshold.\n" \
                  "Inputs do not have to sum to 1"
    _INPUTS = [
        Port("Weights", FLOAT, "The input weights", variable=True)
    ]
    _OUTPUTS = [
        Port("Enter", BOOL, 'Outputs "true" if and only if the sum is greater than the enter threshold'),
        Port("Exit", BOOL, 'Outputs "true" if and only if the sum is less than the exit threshold')
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
        if self.weights.value() is None:
            self.enter.value(False)
            self.exit.value(False)
            return

        try:
            value = sum(self.weights.value())
        except TypeError:
            if not self.datamap[DRY_RUN]:
                log.logErr("Confidence not setup")
            self.enter.value(False)
            self.exit.value(False)
            return

        if not self.datamap[DRY_RUN]:
            log.logInfo(f"{self.datamap[SYMBOL]}: Confidence: {value:.2f}")

        if value >= self.enterThresh.value:
            self.enter.value(True)
        if value <= self.exitThresh.value:
            self.exit.value(True)
