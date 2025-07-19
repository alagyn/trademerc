from nodepasta.argtypes import FLOAT, STRING, NodeArg
from nodepasta.node import Port

from cash_money.nodes.datakeys import LINE_MGR
from cash_money.nodes.cmNode import CMNode
from cash_money.trading.lineManager import LineManager


class PlotNode(CMNode):
    DESCRIPTION = "Logs the input at each timestep for viewing"
    _INPUTS = [Port("Input", FLOAT, "The input value")]
    _ARGS = [NodeArg("Name", STRING, "Name", "Display Name")]
    NODETYPE = "Plot Node"

    def init(self) -> None:
        self.val = self.inputs[0]
        self.key = self.args["Name"].value

    def setup(self) -> None:
        self.lineMgr: LineManager = self.datamap[LINE_MGR]

    def execute(self) -> None:
        val = self.val.value()
        if val is None:
            val = 0
        self.lineMgr.postValue(self.key, val)

    def setupTime(self) -> int:
        return 0
