from .indicator import Indicator
from typing import List, Dict
from .logWrapper import LogWrapper

LOW_PRIORITY = 2
MED_PRIORITY = 1
HIGH_PRIORITY = 0

_PRIORITIES = [HIGH_PRIORITY, MED_PRIORITY, LOW_PRIORITY]


class IndicatorManager:
    def __init__(self, indicators: List[Indicator]):
        self._indicators: Dict[int, List[Indicator]] = {}

        for i in indicators:
            self.addIndicator(i)

        self.logs = LogWrapper()

    def addIndicator(self, i: Indicator):
        if i.priority not in self._indicators:
            self._indicators[i.priority] = []

        self._indicators[i.priority].append(i)

    def addData(self, low: float, close: float, high: float) -> None:
        for p in _PRIORITIES:
            try:
                for i in self._indicators[p]:
                    i.addData(low=low, close=close, high=high)
                    # if i.logging:
                    # i.addLog(self.logs)
            except KeyError:
                pass

    def getLogs(self) -> LogWrapper:
        return self.logs

    def getSetupTime(self) -> int:
        """
        Calculates the min setup time for every created indicator to be properly setup
        :return: The min setup time required
        """
        out = 0
        for p, l in self._indicators.items():
            for i in l:
                out = max(out, i.setupTime())

        return out

    def clearIndicators(self):
        self._indicators.clear()

    def setupIndicators(self, bars):
        for i in range(len(bars)):
            low = bars['low'][i]
            close = bars['close'][i]
            high = bars['high'][i]

            self.addData(low, close, high)
