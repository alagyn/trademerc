from abc import ABC
from nodepasta.node import Node

from typing import Tuple

from cash_money.nodes.datakeys import HIGH, LOW, CLOSE

class CMNode(Node, ABC):
    def __init__(self):
        super(CMNode, self).__init__(noneCapable=True)

    def setupTime(self) -> int:
        raise NotImplementedError

    def hlc(self) -> Tuple[float, float, float]:
        return self.datamap[HIGH], self.datamap[LOW], self.datamap[CLOSE]
