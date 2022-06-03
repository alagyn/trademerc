from abc import ABC
from typing import List, Dict

from cash_money.objects.strategy_params import Param

class CheckParent:
    numChecks: int = 0
    numValFuncs: int = 0
    params: List[Param] = []
    paramDict: Dict[str, Param] = {}

    """
    Base Class for checks that look at indicators
    Extending from this class will not register the check in the
    constructible list for the strategy gui
    """

    def check(self) -> bool:
        """Returns the current check without changing any state"""
        raise NotImplementedError

    def update(self, dry: bool) -> None:
        """Updates the current check's state state"""
        raise NotImplementedError


class Check(CheckParent, ABC):
    @classmethod
    def factory(cls, valFuncs, args) -> CheckParent:
        raise NotImplementedError


