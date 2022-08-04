from nodepasta.argtypes import FLOAT
from nodepasta.node import OutPort

from cash_money.nodes.cmNode import CMNode
from cash_money.nodes.datakeys import HIGH, LOW, CLOSE, VOLUME


class InputNode(CMNode):
    DESCRIPTION = "Outputs the stock values for the current cycle"
    _INPUTS = []
    _OUTPUTS = [
        OutPort("Low", FLOAT, "The cycle's Low"),
        OutPort("Close", FLOAT, "The cycle's Close"),
        OutPort("High", FLOAT, "The cycles's High"),
        OutPort("Volume", FLOAT, "The cycle's Volume")
    ]
    NODETYPE = 'Input'

    def __init__(self):
        super(InputNode, self).__init__()
        self.lo = self.outputs[0]
        self.close = self.outputs[1]
        self.hi = self.outputs[2]
        self.vol = self.outputs[3]

    def setup(self) -> None:
        pass

    def setupTime(self) -> int:
        return 0

    def execute(self) -> None:
        self.lo.setValue(self.datamap[LOW])
        self.close.setValue(self.datamap[CLOSE])
        self.hi.setValue(self.datamap[HIGH])
        self.vol.setValue(self.datamap[VOLUME])
