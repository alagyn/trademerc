from .check import Check
from .maxCheck import MaxCheck
from .minCheck import MinCheck
from .rangeCheck import RangeCheck
from .compareCheck import CompareLessThan, CompareGreaterThan
from .confidenceCheck import ConfidenceCheck
from .crossoverCheck import CrossoverCheck

CHECKS = {x.__name__: x for x in Check.__subclasses__()}
