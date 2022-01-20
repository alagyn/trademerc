from indicators.indicator import Indicator, ValueFunc
from indicators.indicatorManager import HIGH_PRIORITY

AF_INC = 0.02


class ParabolicSAR(Indicator):

    def __init__(self, af: float = 0.02, afMax: float = 0.2, logging: bool = False):
        self._afStart = af
        self._af = af
        self._afMax = afMax
        self._extreme = None
        self._trend = False
        self.psar = ValueFunc('psar')
        self._nextSAR = None

        self._prevHigh = None
        self._prevLow = None

        super().__init__(HIGH_PRIORITY, logging)

    def addData(self, low, close, high) -> None:
        # Start case, takes 2 iterations to setup
        if self._nextSAR is None:
            if self._prevLow is None:
                self._prevLow = close
                return

            # estimated downtrend
            if self._prevLow < close:
                self._trend = False
                self._extreme = low
            # else uptrend
            else:
                self._trend = True
                self._extreme = high

            self._nextSAR = (high + low) / 2
            self._prevLow = low
            self._prevHigh = high
            return

        # Update to today's SAR
        todayPSAR = self._nextSAR

        # Check for a trend switch
        if (self._trend and todayPSAR >= low) or (not self._trend and todayPSAR <= high):
            # Reverse the trend
            self._trend = not self._trend
            todayPSAR = self._extreme
            self._extreme = high if self._trend else low
            self._af = self._afStart

        # Check for new EP, inc AF if found
        if self._trend:
            if high > self._extreme:
                self._extreme = high
                self._af += AF_INC
        else:
            if low < self._extreme:
                self._extreme = low
                self._af += AF_INC

        # limit AF to max
        self._af = min(self._af, self._afMax)

        # calc tomorrow's psar
        self._nextSAR = todayPSAR + self._af * (self._extreme - todayPSAR)

        # Limit tomorrow's psar using ITS prev 2 lows and highs, i.e today's and yesterday's lows
        if self._trend:
            # uptrend, sar should be below prev 2 lows
            self._nextSAR = min(low, self._prevLow, self._nextSAR)
        else:
            # downtrend, sar should be above prev 2 highs
            self._nextSAR = max(high, self._prevHigh, self._nextSAR)

        # Set output psar
        self.psar.set(todayPSAR)
        # update prev vals
        self._prevLow = low
        self._prevHigh = high

    def setupTime(self) -> int:
        return 2
