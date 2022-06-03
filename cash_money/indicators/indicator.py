from typing import Dict, List

from cash_money.objects.strategy_params import Param

_ID_GEN = 1

class Indicator:
    params: List[Param] = []
    paramDict: Dict[str, Param] = {}
    outputs: List[str] = ["INVALID"]

    def __init__(self, indicName: str):
        global _ID_GEN

        self._id = _ID_GEN
        self.name = indicName
        _ID_GEN += 1

    def update(self) -> None:
        raise NotImplementedError

    def setupTime(self) -> int:
        raise NotImplementedError

    def keys(self) -> List[str]:
        return list(self.outputs)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._id == other._id

    def __hash__(self):
        return self._id
