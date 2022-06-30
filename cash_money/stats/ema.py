from cash_money.cmErrors import StatError

class EMA:
    def __init__(self, *, alpha: float = None, period: float = None, smoothing: float = 2):
        self._avg = None
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
        return self._avg

