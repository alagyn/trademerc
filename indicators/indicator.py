from typing import Dict, List
from .logWrapper import LogWrapper
from cmErrors import IndicatorError

_ID_GEN = 1


class ValueFunc:
    def __init__(self, key: str):
        self.key = key
        self.val = None

    def __call__(self) -> float:
        return self.val

    def set(self, val: float):
        self.val = val


class IParam:
    def __init__(self, datatype: type, default):
        self.datatype = datatype
        if not isinstance(default, datatype):
            raise IndicatorError("DEVERR: Defualt indicator param value is wrong type"
                                 f"Expected: {datatype.__name__}, got {type(default)}: '{default}'")
        self.default = default


class DataSelector(IParam):
    def __init__(self):
        super().__init__(str, 'c')


class IndicatorIO:
    def __init__(self, construct: type, params: Dict[str, IParam], outputs: List[str]):
        self.construct = construct
        self.params = params
        self.outputs = outputs

    def __str__(self) -> str:
        return f'{self.construct.__name__}, Params: {self.params}, Outputs: {self.outputs}'


class Indicator:
    params: Dict[str, IParam] = {"INVALID": None}
    outputs: List[str] = ["INVALID"]

    def __init__(self, priority: int):
        global _ID_GEN

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
