import enum


class CrossoverType(enum.IntEnum):
    NONE = enum.auto()
    CROSS_UP = enum.auto()
    CROSS_DOWN = enum.auto()


class Crossover:

    def __init__(self) -> None:
        self.prevDiff = None
        self.curDiff = None

    def check(self, a: float, b: float) -> CrossoverType:
        if self.curDiff is None:
            self.curDiff = a - b
            return CrossoverType.NONE

        self.prevDiff = self.curDiff
        self.curDiff = a - b

        # Upcross
        if self.prevDiff < 0 < self.curDiff:
            return CrossoverType.CROSS_UP
        elif self.prevDiff > 0 > self.curDiff:
            return CrossoverType.CROSS_DOWN
        else:
            return CrossoverType.NONE
