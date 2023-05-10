from cash_money.nodes.cmNode import CMNode
from cash_money.trading.objects import Bar, Stock, StockStatus, Action, BuyAction, UpdateStopAction, HoldAction, SellAction
from cash_money.nodes.datakeys import *
from cash_money.utils.node_utils import registerNodes

import logging

from nodepasta.nodegraph import NodeGraph

log = logging.getLogger("NodeStrategy")


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
        self.nodegraph.datamap[ENTRY] = False
        self.nodegraph.datamap[EXIT] = False

        if stock.bar is None:
            log.warn(
                f"stock.bar is None: {stock.symbol}, trade day: {tradeDay}"
            )
            return HoldAction(stock)

        self.nodegraph.execute()
        pos = stock.status()

        stop = self.nodegraph.datamap[STOP]

        if pos == StockStatus.InMarket:
            if self.nodegraph.datamap[EXIT]:
                return SellAction(stock)

            if stop is not None and tradeDay >= self.nextStopUpdate:
                self.nextStopUpdate = tradeDay + self.stopPeriod
                return UpdateStopAction(stock, stop)

            return HoldAction(stock)

        elif pos == StockStatus.OutMarket:
            if self.nodegraph.datamap[ENTRY]:
                if stop is None:
                    return BuyAction(stock, None)
                else:
                    self.nextStopUpdate = tradeDay + self.stopPeriod
                    return BuyAction(stock, stop)

        return HoldAction(stock)

    def getSetupTime(self) -> int:
        stratNode: CMNode = self.nodegraph.datamap[STRAT_NODE]
        return stratNode.recurseSetupTime()
