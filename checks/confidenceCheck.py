from checks.check import Check
from typing import List, Tuple
from cmErrors import CheckError


class _WeightedCheck:
    def __init__(self, check: Check, weight: float):
        self._c = check
        self._w = weight

    def check(self) -> bool:
        return self._c.check()

    def weight(self) -> float:
        return self._w

    def __str__(self):
        return str(self._c)


class ConfidenceCheck(Check):

    def __init__(self, minConf, maxConf=1.0, checks: List[Tuple[Check, float]] = None):
        self._checks: List[_WeightedCheck] = []

        self._totalWeight = 0
        self._minConf = minConf
        self._maxConf = maxConf

        if checks is not None:
            for x in checks:
                self.addCheck(*x)


    @classmethod
    def factory(cls, valFuncs, checks, args):
        confs = args['confs']

        if len(confs) != len(checks):
            raise CheckError("Len of checks not equal to len of confidences")

        return ConfidenceCheck(
            minConf=args['minConf'],
            maxConf=args['maxConf'],
            checks=list(zip(checks, confs))
        )

    def addCheck(self, check: Check, weight: float):
        self._checks.append(_WeightedCheck(check, weight))
        self._totalWeight += weight

    def confidence(self):
        out = 0
        for c in self._checks:
            val = c.check()
            if val:
                out += c.weight()
            # print(c, val)

        return out / self._totalWeight

    def check(self) -> bool:
        return self._minConf <= self.confidence() <= self._maxConf
