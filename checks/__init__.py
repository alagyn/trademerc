from .check import Check
from .maxCheck import MaxCheck
from .minCheck import MinCheck
from .rangeCheck import RangeCheck
from .compareCheck import Compare
from .crossoverCheck import CrossoverCheck
from .confidence import Confidence
from typing import Dict

CHECKS: Dict[str, Check] = {x.__name__: x for x in Check.__subclasses__()}

for _x in Check.__subclasses__():
    for _p in _x.params:
        _p.parentName = _x.__name__
        _x.paramDict[_p.paramName] = _p