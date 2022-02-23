from .indicator import Indicator, ValueFunc
from .barValue import BarValue
from .ema import EMA
from .averageTrueRange import AverageTrueRange
from .macd import MACD
from .parabolicSAR import ParabolicSAR
from .smma import SMMA
from .sma import SMA
from .stochastic import Stochastic

from .indicator import Indicator
from typing import Dict, Type
from cmErrors import IndicatorError

INDICATORS: Dict[str, Type[Indicator]] = {x.__name__: x for x in Indicator.__subclasses__()}

for _x in Indicator.__subclasses__():
    if _x.outputs[0] == 'INVALID':
        raise IndicatorError(f'DEVERR: {_x.__name__}, outputs not initialized')
    for _p in _x.params:
        _p.parentName = _x.__name__
        _x.paramDict[_p.paramName] = _p
