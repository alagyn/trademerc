from .ema import EMA

class SMMA:
    """
    SMMA is equivalent to an EMA with alpha = 1/period
    """

    def __init__(self, period: int):
        self._a = 1 / period
        self._ema = EMA(alpha=self._a)
        self._p = period

    def next(self, data) -> float:
        return self._ema.next(data)

    def getValue(self) -> float:
        return self._ema.getValue()

    def setupTime(self) -> int:
        return self._p
