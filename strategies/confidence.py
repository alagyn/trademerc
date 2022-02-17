from checks.check import Check
from typing import List, Tuple
from cmErrors import CheckError


class _WeightedCheck:
    def __init__(self, check: Check, weight: float):
        self._c = check
        self.w = weight

    def check(self) -> bool:
        return self._c.check()

    def update(self) -> bool:
        return self._c.update()

    def __str__(self):
        return str(self._c)


class Confidence:

    def __init__(self, minConf, maxConf=1.0, checks: List[Tuple[Check, float]] = None):
        self._checks: List[_WeightedCheck] = []

        self._totalWeight = 0
        self._minConf = minConf
        self._maxConf = maxConf

        if checks is not None:
            for x in checks:
                self.addCheck(*x)

    @classmethod
    def factory(cls, _valFuncs, checks, args):
        confs = args['confs']

        if len(confs) != len(checks):
            raise CheckError("Len of checks not equal to len of confidences")

        return Confidence(
            minConf=args['minConf'],
            maxConf=args['maxConf'],
            checks=list(zip(checks, confs))
        )

    def addCheck(self, check: Check, weight: float):
        self._checks.append(_WeightedCheck(check, weight))

        # Allow for negative weights, but they don't contribute to total
        if weight > 0:
            self._totalWeight += weight

    def update(self) -> bool:
        for c in self._checks:
            c.update()

        return self.check()

    def confidence(self):
        out = 0

        # TODO remove templist
        templist = []

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
                out -= c.w

            templist.append(val)

        # print(f'Sum: {out}, TotalW: {self._totalWeight}')
        # out /= self._totalWeight
        # print(f'Final: {out}')
        # exit()
        return out, templist

    def check(self) -> bool:
        c, _ = self.confidence()
        return self._minConf <= c <= self._maxConf
