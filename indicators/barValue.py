from indicators.indicator import Indicator, ValueFunc
from indicators.indicatorManager import HIGH_PRIORITY
from objects.bar import Bar

_LOW = 'Low'
_CLOSE = 'Close'
_HIGH = 'High'


class BarValue(Indicator):
    params = {}
    outputs = [_LOW, _CLOSE, _HIGH]

    def __init__(self):
        self.low = ValueFunc(_LOW)
        self.close = ValueFunc(_CLOSE)
        self.high = ValueFunc(_HIGH)

        super(BarValue, self).__init__(HIGH_PRIORITY)

    def addData(self, bar: Bar) -> None:
        self.low.set(bar.lo)
        self.close.set(bar.close)
        self.high.set(bar.hi)

    def setupTime(self) -> int:
        return 1
