from abc import ABC
from nodepasta.node import Node

from typing import Tuple, Dict

from cash_money.nodes.datakeys import HIGH, LOW, CLOSE

class CMNode(Node, ABC):
    def __init__(self):
        super(CMNode, self).__init__(noneCapable=True)

    def setupTime(self) -> int:
        raise NotImplementedError

    def recurseSetupTime(self, cachemap: Dict[int, int] = None) -> int:
        if cachemap is None:
            cachemap = {}

        cost = 0
        for link in self.incoming():
            # noinspection PyTypeChecker
            parent: CMNode = link.parent
            try:
                parentCost = cachemap[parent.nodeID]
            except KeyError:
                parentCost = parent.recurseSetupTime(cachemap)

            cost = max(cost, parentCost)

        total = cost + self.setupTime()
        cachemap[self.nodeID] = total

        return total

    def hlc(self) -> Tuple[float, float, float]:
        return self.datamap[HIGH], self.datamap[LOW], self.datamap[CLOSE]
