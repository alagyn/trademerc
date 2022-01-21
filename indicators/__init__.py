from .indicator import Indicator, ValueFunc
from .barValue import BarValue
from .ema import EMA
from .averageTrueRange import AverageTrueRange
from .macd import MACD
from .parabolicSAR import ParabolicSAR
from .smma import SMMA
from .sma import SMA
from .stochastic import Stochastic

from .indicator import Indicator, IndicatorIO

# INDICATORS = {x.__name__: x for x in Indicator.__subclasses__()}
INDICATORS = {x.__name__: IndicatorIO(x, x.params, x.outputs) for x in Indicator.__subclasses__()}

