from cash_money.nodes.cmNode import CMNode
from cash_money.objects.bar import Bar
from cash_money.objects.stock import Stock, StockStatus
from cash_money.objects.action import Action
from cash_money.nodes.datakeys import *
from cash_money.utils.node_utils import registerNodes

from cash_money.utils.log_utils import CMLogger

from nodepasta.nodegraph import NodeGraph

log = CMLogger("NodeStrategy")


class NodeStrategy:
    def __init__(self, jGraph, symbol: str):
        self.nodegraph = NodeGraph()
        registerNodes(self.nodegraph)
        self.nodegraph.loadFromJSON(jGraph)
        self.nodegraph.setupNodes()

        self.nodegraph.datamap[SYMBOL] = symbol

        self.stopPeriod = self.nodegraph.datamap[STOP_PERIOD]
        self.nextStopUpdate = 0

    def addData(self, bar: Bar):
        self.nodegraph.datamap[LOW] = bar.lo
        self.nodegraph.datamap[CLOSE] = bar.close
        self.nodegraph.datamap[HIGH] = bar.hi
        self.nodegraph.datamap[VOLUME] = bar.vol

    def dryRun(self):
        self.nodegraph.datamap[DRY_RUN] = True
        self.nodegraph.execute()
        self.nodegraph.datamap[DRY_RUN] = False

    def nextAction(self, tradeDay: int, stock: Stock) -> Action:
        self.nodegraph.execute()
        pos = stock.status()

        stop = self.nodegraph.datamap[STOP]

        if pos == StockStatus.InMarket:
            if self.nodegraph.datamap[EXIT]:
                return stock.sell()

            if stop is not None and tradeDay >= self.nextStopUpdate:
                self.nextStopUpdate = tradeDay + self.stopPeriod
                return stock.updateStop(stop, stop * 0.8)

            return stock.hold()

        elif pos == StockStatus.OutMarket:
            if self.nodegraph.datamap[ENTRY]:

                if stop is None:
                    return stock.buy()
                else:
                    self.nextStopUpdate = tradeDay + self.stopPeriod
                    return stock.buyAndStop(stop, stop * 0.8)

        return stock.hold()

    def getSetupTime(self) -> int:
        stratNode: CMNode = self.nodegraph.datamap[STRAT_NODE]
        return stratNode.recurseSetupTime()
