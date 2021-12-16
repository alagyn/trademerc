from typing import Callable, Dict, List

ValueFunc = Callable[[], float]

_ID_GEN = 1

LOW_PRIORITY = 2
MED_PRIORITY = 1
HIGH_PRIORITY = 0

_PRIORITIES = [HIGH_PRIORITY, MED_PRIORITY, LOW_PRIORITY]


class Indicator:
    def __init__(self, priority: int):
        global _ID_GEN

        self.priority = priority
        self._id = _ID_GEN
        _ID_GEN += 1

    def set(self, symbol: str):
        _register(self, symbol)
        return self

    def addData(self, *, low=None, close=None, high=None) -> None:
        raise NotImplementedError

    def setupTime(self) -> int:
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._id == other._id

    def __hash__(self):
        return self._id


# symbol -> priority -> list indicators
_INDICATORS: Dict[str, Dict[int, List[Indicator]]] = {}


def addData(symbol: str, low: float, close: float, high: float) -> None:
    global _INDICATORS, _PRIORITIES

    if symbol not in _INDICATORS:
        return

    for p in _PRIORITIES:
        try:
            for i in _INDICATORS[symbol][p]:
                i.addData(low=low, close=close, high=high)
        except KeyError:
            pass


def getSetupTime() -> int:
    """
    Calculates the min setup time for every created indicator to be properly setup
    :return: The min setup time required
    """
    out = 0
    for symb, ps in _INDICATORS.items():
        for p, l in ps.items():
            for i in l:
                out = max(out, i.setupTime())

    return out


def _register(i: Indicator, symbol: str):
    if symbol not in _INDICATORS:
        newsymb = {i.priority: [i]}
        _INDICATORS[symbol] = newsymb
    else:
        symb = _INDICATORS[symbol]
        if i.priority in symb:
            symb[i.priority].append(i)
        else:
            symb[i.priority] = [i]
