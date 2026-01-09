from nodepasta.argtypes import FLOAT
from nodepasta.node import Port

from cash_money.nodes.cmNode import CMNode
from cash_money.nodes.datakeys import HIGH, LOW, CLOSE, VOLUME, PREV_STOP


class InputNode(CMNode):
    DESCRIPTION = "Outputs the stock values for the current cycle"
    _INPUTS = []
    _OUTPUTS = [
        Port("Low", FLOAT, "The cycle's Low"),
        Port("Close", FLOAT, "The cycle's Close"),
        Port("High", FLOAT, "The cycles's High"),
        Port("Volume", FLOAT, "The cycle's Volume"),
        Port("Stop-Loss", FLOAT, "The current stop-loss price")
    ]
    NODETYPE = 'Input'

    def init(self):
        self.lo = self.outputs[0]
        self.close = self.outputs[1]
        self.hi = self.outputs[2]
        self.vol = self.outputs[3]
        self.stop = self.outputs[4]

    def setup(self) -> None:
        pass

    def setupTime(self) -> int:
        return 0

    def execute(self) -> None:
        self.lo.value(self.datamap[LOW])
        self.close.value(self.datamap[CLOSE])
        self.hi.value(self.datamap[HIGH])
        self.vol.value(self.datamap[VOLUME])
        self.stop.value(self.datamap[PREV_STOP])
