from typing import List, Dict

from objects.strategy_params import Param


class Check:
    numChecks: int = 0
    numValFuncs: int = 0
    params: List[Param] = []
    paramDict:  Dict[str, Param] = {}

    """
    Base Class for checks that look at indicators
    """
    def check(self) -> bool:
        """Returns the current check without changing any state"""
        raise NotImplementedError

    def update(self) -> None:
        """Updates the current check's state state"""
        raise NotImplementedError

    @classmethod
    def factory(cls, valFuncs, checks, args):
        raise NotImplementedError