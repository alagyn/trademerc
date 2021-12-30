
from .check import Check
from .maxCheck import MaxCheck
from .minCheck import MinCheck
from .rangeCheck import RangeCheck
from .compareCheck import CompareLessThan, CompareGreaterThan
from .confidenceCheck import ConfidenceCheck

CHECK_NAMES = []
for x in Check.__subclasses__():
    CHECK_NAMES.append(x.__name__)
