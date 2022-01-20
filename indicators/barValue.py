from indicators.indicator import Indicator, ValueFunc
from indicators.indicatorManager import HIGH_PRIORITY


class BarValue(Indicator):

    def __init__(self):
        self.low = ValueFunc('low')
        self.close = ValueFunc('close')
        self.high = ValueFunc('high')

        super(BarValue, self).__init__(HIGH_PRIORITY, False)


    def addData(self, low, close, high) -> None:
        self.low.set(low)
        self.close.set(close)
        self.high.set(high)

    def setupTime(self) -> int:
        return 1
