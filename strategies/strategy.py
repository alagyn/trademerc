from checks.checkManager import CheckManager
from indicators.logWrapper import LogWrapper
from objects.stock import Stock
from objects.action import Action
from objects.bar import Bar
from indicators.indicatorManager import IndicatorManager


class Strategy:
    def __init__(self, symbol: str, name: str, iManage: IndicatorManager, cManage: CheckManager):
        self.symbol = symbol
        self.name = name
        self.iManage = iManage
        self.cManage = cManage
        self.bar = None

    def getName(self):
        return self.name

    def addData(self, low: float, close: float, high: float, dry: bool = False) -> None:
        self.iManage.addData(low, close, high)
        self.cManage.update(dry)
        self.bar = Bar(low, close, high)

    def getSetupTime(self) -> int:
        return self.iManage.getSetupTime()

    def setupIndicators(self, bars):
        self.iManage.setupIndicators(bars)

    def nextAction(self, day: int, stock: Stock) -> Action:
        raise NotImplementedError

    def getLogs(self) -> LogWrapper:
        return self.iManage.getLogs()
