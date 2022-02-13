from typing import List

from objects.strategy_params import Param


class Check:
    numChecks: int = 0
    numValFuncs: int = 0
    params: List[Param] = []


    """
    Base Class for checks that look at indicators
    """
    def check(self) -> bool:
        """Returns the current check without changing any state"""
        raise NotImplementedError

    def update(self) -> bool:
        """Returns the current check, possibly changing state"""
        raise NotImplementedError

    @classmethod
    def factory(cls, valFuncs, checks, args):
        raise NotImplementedError