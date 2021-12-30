from checks.check import Check
from typing import List, Tuple


class ConfidenceCheck(Check):

    def __init__(self, minConf, maxConf=1.0, checks: List[Tuple[Check, float]] = None):
        self._checks: List[ConfidenceCheck.WeightedCheck] = []

        self._totalWeight = 0
        self._minConf = minConf
        self._maxConf = maxConf

        if checks is not None:
            for x in checks:
                self.addCheck(*x)

    class WeightedCheck:
        def __init__(self, check: Check, weight: float):
            self._c = check
            self._w = weight

        def check(self) -> bool:
            return self._c.check()

        def weight(self) -> float:
            return self._w

    def addCheck(self, check: Check, weight: float):
        self._checks.append(self.WeightedCheck(check, weight))
        self._totalWeight += weight

    def confidence(self):
        out = 0
        for c in self._checks:
            if c.check():
                out += c.weight()

        return out / self._totalWeight

    def check(self) -> bool:
        return self._minConf <= self.confidence() <= self._maxConf
