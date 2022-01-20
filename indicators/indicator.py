from typing import Dict, List
from .logWrapper import LogWrapper

_ID_GEN = 1


class ValueFunc:
    def __init__(self, key: str):
        self.key = key
        self.val = None

    def __call__(self) -> float:
        return self.val

    def set(self, val: float):
        self.val = val


class Indicator:
    def __init__(self, priority: int, logging: bool):
        global _ID_GEN

        self.logging = logging
        self.priority = priority
        self._id = _ID_GEN
        _ID_GEN += 1
        self._values: Dict[str, ValueFunc] = {}

        for name in dir(self):
            if not name.startswith('__'):
                x = getattr(self, name)
                if isinstance(x, ValueFunc):
                    self._values[x.key] = x


    def addLog(self, logs: LogWrapper) -> None:
        for name, v in self._values.values():
            logs[name] = v()

    def addData(self, low, close, high) -> None:
        raise NotImplementedError

    def setupTime(self) -> int:
        raise NotImplementedError

    def keys(self) -> List[str]:
        return list(self._values.keys())

    def __getitem__(self, item) -> ValueFunc:
        return self._values[item]

    def __contains__(self, item) -> bool:
        return item in self._values

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._id == other._id

    def __hash__(self):
        return self._id


