from nodepasta.argtypes import BOOL, FLOAT, INT
from nodepasta.node import InPort, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.nodes.datakeys import ENTRY, EXIT, STOP, STOP_PERIOD

_STOP_P = "stopPeriod"

class StrategyNode(CMNode):
    _INPUTS = [
        InPort("Entry Condition", BOOL),
        InPort("Exit Condition", BOOL),
        InPort("Stop-Loss Price", FLOAT)
    ]
    _ARGS = [
        NodeArg(_STOP_P, INT, "Stop Update Period", value=1)
    ]
    NODETYPE = "Strategy"

    def __init__(self):
        super(StrategyNode, self).__init__()
        self.entry = self.inputs[0]
        self.exit = self.inputs[1]
        self.stop = self.inputs[2]

    def setup(self) -> None:
        self.datamap[STOP_PERIOD] = self.args[_STOP_P].value

    def setupTime(self) -> int:
        return 0

    def execute(self) -> None:
        self.datamap[ENTRY] = self.entry.value
        self.datamap[EXIT] = self.exit.value
        self.datamap[STOP] = self.stop.value
