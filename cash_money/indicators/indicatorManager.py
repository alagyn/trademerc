from collections import deque
from typing import List, Deque, Set, Dict

from .indicator import Indicator
from .logWrapper import LogWrapper
from .lineManager import LineManager
from cash_money.cmErrors import IndicatorError


class IndicatorManager:
    def __init__(self, indicators: List[Indicator], lineManager: LineManager):
        self._indicators: Deque[Indicator] = deque()
        self._indicLookup: Dict[str, Indicator] = {}

        for i in indicators:
            self.addIndicator(i)

        self.logs = LogWrapper()
        self.lineManager = lineManager

    def addIndicator(self, i: Indicator):
        if i.name in self._indicLookup:
            raise IndicatorError(f'Duplicate indicator name "{i.name}')
        self._indicators.append(i)
        self._indicLookup[i.name] = i

    def recurSort(self, newQ: Deque[Indicator], curI, ahead: Set[str], behind: Set[str]):
        behind.add(curI.name)
        for request in self.lineManager.requests[curI.name]:
            nextIName = self.lineManager.registers[request]
            if nextIName in behind:
                raise IndicatorError(f'Indicator Circular dependency detected: '
                                     f'{curI.name} and {nextIName}, line: {request}')
            if nextIName in ahead:
                # Indicator is already ahead of this one, skip
                continue

            nextI = self._indicLookup[nextIName]
            self.recurSort(newQ, nextI, ahead, behind)

        behind.remove(curI.name)
        ahead.add(curI.name)
        newQ.append(curI)

    def errorCheckAndSort(self):
        self.lineManager.errorCheck()
        newQ = deque()
        ahead = set()
        behind = set()

        while len(self._indicators) > 0:
            i = self._indicators.pop()
            if i.name in ahead:
                # Skip indicators already in the new q
                continue

            self.recurSort(newQ, i, ahead, behind)

        self._indicators = newQ

    def update(self, low: float, close: float, high: float, volume: float) -> None:
        self.lineManager.update(low, close, high, volume)

        for i in self._indicators:
            # Let errors back propagate
            i.update()

    def getLogs(self) -> LogWrapper:
        return self.logs

    def getSetupTime(self) -> int:
        """
        Calculates the min setup time for every created indicator to be properly setup
        :return: The min setup time required
        """
        out = 0
        for p, l in self._indicators:
            for i in l:
                out = max(out, i.setupTime())

        return out

    def clearIndicators(self):
        self._indicators.clear()
