from typing import List, Dict, Any
import os
import json
import logging

from .fileSelect import askOpenFile, askSaveFile
from cash_money.utils.file_utils import loadStockFile, loadStratFile
from cash_money.utils.node_utils import registerNodes, newStrat, defaultStratData

from nodepasta.nodegraph import NodeGraph
import nodepasta.impasta.imgui_node_graph as imgui_node_graph
from nodepasta.impasta.imgui_arg_handlers import getDefaultArgHandlers
from nodepasta.argtypes import INT, FLOAT, BOOL

import imgui as im

log = logging.getLogger("UI-State")

CACHE_STOCKS = "stock_file"
CACHE_STRAT = "strat_file"


class UIState:

    def __init__(self, cachedata: Dict[str, Any]) -> None:
        self.stratFile = ""
        self.stockFile = ""
        self.stocks: List[str] = []

        self.stratGraph = NodeGraph()
        registerNodes(self.stratGraph)

        self.stratName = im.StrRef(256)

        try:
            self.loadStocks(cachedata[CACHE_STOCKS])
        except KeyError:
            pass

        self.stratData = defaultStratData()
        try:
            self.loadStrat(cachedata[CACHE_STRAT])
        except KeyError:
            pass

        self.imNodeGraph: imgui_node_graph.ImNodeGraph = None  # type: ignore

    def init(self):
        self.imNodeGraph = imgui_node_graph.ImNodeGraph(self.stratGraph)

        self.imNodeGraph.registerTypeColor(FLOAT, im.Vec4(1.0, 0.5, 0.5, 1.0))
        self.imNodeGraph.registerTypeColor(INT, im.Vec4(0.144, 1.0, 0, 1.0))
        self.imNodeGraph.registerTypeColor(BOOL, im.Vec4(0.03, 0.9, 1.0, 1.0))

        for k, v in getDefaultArgHandlers().items():
            self.imNodeGraph.registerArgHandler(k, v)

    def loadStrat(self, file):
        if os.path.exists(file):
            self.stratFile = file
            self.stratData = loadStratFile(self.stratFile)
            self.stratName.set(self.stratData['name'])
            self.stratGraph.loadFromJSON(self.stratData['graph'])
        else:
            log.warn("Could not open strat file '%s'", file)
            self.newStrat()

    def askStrat(self):
        f = askOpenFile("Select Strategy", [('Strategy', '.strat')])
        if len(f) > 0:
            self.loadStrat(f)

    def askSaveStrat(self):
        f = askSaveFile("Save Strategy", self.stratFile, [('Strategy', '.strat')])
        if len(f) > 0:
            self.stratFile = f
            self.saveStrat()

    def saveStrat(self):
        if len(self.stratFile) == 0:
            self.askSaveStrat()
        else:
            data = self.stratGraph.getJSON()

            with open(self.stratFile, mode='w') as f:
                json.dump({
                    "name": self.stratName.view(),
                    "graph": data
                }, f)
            self.imNodeGraph.needToSave = False

    def newStrat(self):
        self.stratFile = "newStrat.strat"
        self.stratGraph.clear()
        newStrat(self.stratGraph)

    def loadStocks(self, file):
        if os.path.exists(file):
            self.stockFile = file
            self.stocks = loadStockFile(self.stockFile)
        else:
            log.warn("Could not open stock file '%s'", file)
            self.stockFile = ""

    def askStocks(self):
        f = askOpenFile("Select Stocks", [("Text", ".txt")])
        if len(f) > 0:
            self.loadStocks(f)

    def toCache(self, cache: Dict[str, Any]):
        cache[CACHE_STOCKS] = self.stockFile
        cache[CACHE_STRAT] = self.stratFile
