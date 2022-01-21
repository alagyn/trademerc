from indicators.indicator import Indicator, ValueFunc
from indicators.indicatorManager import HIGH_PRIORITY

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

    def addData(self, low, close, high) -> None:
        self.low.set(low)
        self.close.set(close)
        self.high.set(high)

    def setupTime(self) -> int:
        return 1
