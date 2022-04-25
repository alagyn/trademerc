from checks.check import Check, CheckParent
from typing import List, Tuple


class _WeightedCheck:
    def __init__(self, check: Check, weight: float):
        self._c = check
        self.w = weight

    def check(self) -> bool:
        return self._c.check()

    def update(self, dry: bool):
        self._c.update(dry)

    def __str__(self):
        return str(self._c)


class Confidence(CheckParent):

    def __init__(self, minConf, maxConf=1.0, checks: List[Tuple[CheckParent, float]] = None):
        self._checks: List[_WeightedCheck] = []

        self._totalWeight = 0
        self._minConf = minConf
        self._maxConf = maxConf

        if checks is not None:
            for x in checks:
                self.addCheck(*x)

    def addCheck(self, check: Check, weight: float):
        self._checks.append(_WeightedCheck(check, weight))

        # Allow for negative weights, but they don't contribute to total
        if weight > 0:
            self._totalWeight += weight

    def update(self, dry: bool):
        for c in self._checks:
            c.update(dry)

    def confidence(self):
        out = 0

        # TODO remove templist
        # templist = []

        for c in self._checks:
            val = bool(c.check())
            # print(c, val)
            # if check is good add weight (both pos and neg)
            if val:
                # print(f'Adding: {c.w}')
                out += c.w
            # if check is bad and weight is pos, sub weight
            if not val:
                # print(f'Subbing: {c.w}')
                # out -= c.w
                pass

            # templist.append(val)

        # print(f'Sum: {out}, TotalW: {self._totalWeight}')
        # out /= self._totalWeight
        # print(f'Final: {out}')
        # exit()
        # return out, templist
        return out

    def check(self) -> bool:
        # c, _ = self.confidence()
        c =self.confidence()
        c = round(c, 3)
        return self._minConf <= c <= self._maxConf
