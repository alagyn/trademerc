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

for x in Indicator.__subclasses__():
    if x.outputs[0] == 'INVALID':
        raise IndicatorError(f'DEVERR: {x.__name__}, outputs not initialized')
    for p in x.params:
        p.parentName = x.__name__
