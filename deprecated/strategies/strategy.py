from cash_money.checks.checkManager import CheckManager
from cash_money.indicators.logWrapper import LogWrapper
from cash_money.objects.stock import Stock
from cash_money.objects.action import Action
from cash_money.indicators.indicatorManager import IndicatorManager


class Strategy:
    def __init__(self, symbol: str, name: str, iManage: IndicatorManager, cManage: CheckManager):
        self.symbol = symbol
        self.name = name
        self._iManage = iManage
        self._cManage = cManage
        self.bar = None

    def getName(self):
        return self.name

    def addData(self, data, dry: bool = False) -> None:
        self._iManage.update(**data)
        self._cManage.update(dry)


    def getSetupTime(self) -> int:
        return self._iManage.getSetupTime()

    def setupIndicators(self, bars):
        for b in bars:
            self.addData(b, True)

    def nextAction(self, day: int, stock: Stock) -> Action:
        raise NotImplementedError

    def getLogs(self) -> LogWrapper:
        return self._iManage.getLogs()
