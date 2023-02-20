from typing import Optional

from cash_money.cmErrors import StatError


class EMA:
    """
    Exponential Moving Average
    """

    def __init__(self, *, alpha: Optional[float] = None, period: Optional[float] = None, smoothing: float = 2):
        self._avg: Optional[float] = None
        if alpha is not None:
            self._a = alpha
        elif period is None or smoothing is None:
            raise StatError('Alpha or period and smoothing not supplied')
        else:
            self._a = smoothing / (period + 1)

        self._ia = 1 - self._a

    def next(self, data) -> float:
        if self._avg is None:
            self._avg = data
        else:
            self._avg = data * self._a + self._avg * self._ia
        return self._avg

    def getValue(self) -> float:
        if self._avg is None:
            return 0.0
        return self._avg
