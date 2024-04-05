from nodepasta.node import Node

from typing import Tuple, Dict, Optional

from cash_money.nodes.datakeys import HIGH, LOW, CLOSE


class CMNode(Node):

    def setupTime(self) -> int:
        raise NotImplementedError

    def recurseSetupTime(self, cachemap: Optional[Dict[int, int]] = None) -> int:
        if cachemap is None:
            cachemap = {}

        cost = 0
        for link in self.incoming():
            parent: CMNode = link.pPort.node  # type: ignore
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
