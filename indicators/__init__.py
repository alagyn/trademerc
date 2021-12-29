
from .indicator import Indicator
from .dayValue import DayValue
from .ema import EMA
from .crossover import Crossover
from .averageTrueRange import AverageTrueRange
from .macd import MACD
from .parabolicSAR import ParabolicSAR
from .smma import SMMA
from .sma import SMA
from .stochastic import Stochastic

from .indicator import Indicator

INDICATORS = []
for x in Indicator.__subclasses__():
    INDICATORS.append(x)