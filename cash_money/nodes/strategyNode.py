from nodepasta.argtypes import BOOL, FLOAT, INT
from nodepasta.node import Port, NodeArg
from nodepasta.errors import NodeDefError

from cash_money.nodes.cmNode import CMNode
from cash_money.nodes.datakeys import ENTRY, EXIT, STOP, STOP_PERIOD, STRAT_NODE

_STOP_P = "stopPeriod"


class StrategyNode(CMNode):
    DESCRIPTION = "The output of the strategy graph."
    _INPUTS = [
        Port("Entry Condition", BOOL, "When set to true, signals a buy action if out of market"),
        Port("Exit Condition", BOOL, "When set to true, signals a sell action if in market"),
        Port("Stop-Loss Price", FLOAT, "Used to set the value of the stop-loss order when buying/updating")
    ]
    _ARGS = [
        NodeArg(_STOP_P, INT, "Stop Update Period", "The number of cycles before the stop-loss order is updated",
                value=1)
    ]
    NODETYPE = "Strategy"

    def __init__(self):
        super(StrategyNode, self).__init__()
        self.entry = self.inputs[0]
        self.exit = self.inputs[1]
        self.stop = self.inputs[2]

    def setup(self) -> None:
        if STRAT_NODE in self.datamap:
            raise NodeDefError("StrategyNode.init()", f"More than one strategy node defined:\n"
                                                      f"{self.datamap[STRAT_NODE]}\n"
                                                      f"{self}")
        self.datamap[STRAT_NODE] = self
        self.datamap[STOP_PERIOD] = self.args[_STOP_P].value

    def setupTime(self) -> int:
        return 0

    def execute(self) -> None:
        self.datamap[ENTRY] = self.entry.value()
        self.datamap[EXIT] = self.exit.value()
        self.datamap[STOP] = self.stop.value()
