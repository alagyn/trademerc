from typing import Dict, List

_ID_GEN = 1


class _ValueFuncWrapper:
    def __init__(self, key: str, func):
        self.key = key
        self.func = func
        self.ref = None

    def __call__(self) -> float:
        return self.func(self.ref)


class ValueFunc:
    def __init__(self, key: str):
        self.key = key

    def __call__(self, func):
        return _ValueFuncWrapper(self.key, func)


class Indicator:
    def __init__(self, priority: int):
        global _ID_GEN

        self.priority = priority
        self._id = _ID_GEN
        _ID_GEN += 1
        self._values: Dict[str, _ValueFuncWrapper] = {}

        for name in dir(self):
            x = getattr(self, name)
            if isinstance(x, _ValueFuncWrapper):
                self._values[x.key] = x
                x.ref = self


    def set(self, symbol: str):
        IndicatorManager().register(self, symbol)
        return self

    def addData(self, *, low=None, close=None, high=None) -> None:
        raise NotImplementedError

    def setupTime(self) -> int:
        raise NotImplementedError

    def keys(self) -> List[str]:
        return list(self._values.keys())

    def __getitem__(self, item) -> _ValueFuncWrapper:
        return self._values[item]

    def __contains__(self, item) -> bool:
        return item in self._values

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._id == other._id

    def __hash__(self):
        return self._id


LOW_PRIORITY = 2
MED_PRIORITY = 1
HIGH_PRIORITY = 0

_PRIORITIES = [HIGH_PRIORITY, MED_PRIORITY, LOW_PRIORITY]


class IndicatorManager:
    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)

            # symbol -> priority -> list indicators
            cls._inst._indicators = {}

        return cls._inst

    def register(self, i: Indicator, symbol: str):
        if symbol not in self._indicators:
            newsymb = {i.priority: [i]}
            self._indicators[symbol] = newsymb
        else:
            symb = self._indicators[symbol]
            if i.priority in symb:
                symb[i.priority].append(i)
            else:
                symb[i.priority] = [i]

    def addData(self, symbol: str, low: float, close: float, high: float) -> None:
        if symbol not in self._indicators:
            return

        for p in _PRIORITIES:
            try:
                for i in self._indicators[symbol][p]:
                    i.addData(low=low, close=close, high=high)
            except KeyError:
                pass

    def getSetupTime(self) -> int:
        """
        Calculates the min setup time for every created indicator to be properly setup
        :return: The min setup time required
        """
        out = 0
        for symb, ps in self._indicators.items():
            for p, l in ps.items():
                for i in l:
                    out = max(out, i.setupTime())

        return out

    def clearIndicators(self):
        self._indicators.clear()

    def setupIndicators(self, bars):
        for i in range(len(bars)):
            for x in bars:
                low = bars[x]['low'][i]
                close = bars[x]['close'][i]
                high = bars[x]['high'][i]

                self.addData(x, low, close, high)
