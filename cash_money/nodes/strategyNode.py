from nodepasta.argtypes import BOOL
from nodepasta.node import InPort

from cash_money.nodes.cmNode import CMNode
from cash_money.nodes.datakeys import ENTRY, EXIT


class StrategyNode(CMNode):
    _INPUTS = [
        InPort("Entry Condition", BOOL),
        InPort("Exit Condition", BOOL)
    ]
    NODETYPE = "Strategy"

    def __init__(self):
        super(StrategyNode, self).__init__()
        self.entry = self.inputs[0]
        self.exit = self.inputs[1]

    def setup(self) -> None:
        pass

    def setupTime(self) -> int:
        return 0

    def execute(self) -> None:
        self.datamap[ENTRY] = self.entry.value
        self.datamap[EXIT] = self.exit.value
