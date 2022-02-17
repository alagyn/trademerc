from .check import Check
from .maxCheck import MaxCheck
from .minCheck import MinCheck
from .rangeCheck import RangeCheck
from .compareCheck import Compare
from .confidenceCheck import ConfidenceCheck
from .crossoverCheck import CrossoverCheck
from typing import Dict

CHECKS: Dict[str, Check] = {x.__name__: x for x in Check.__subclasses__()}

for x in Check.__subclasses__():
    for p in x.params:
        p.parentName = x.__name__