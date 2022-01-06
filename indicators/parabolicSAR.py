from indicators.indicator import Indicator, HIGH_PRIORITY, ValueFunc

AF_INC = 0.02


class ParabolicSAR(Indicator):

    def __init__(self, af: float = 0.02, afMax: float = 0.2):
        super().__init__(HIGH_PRIORITY)

        self.afStart = af
        self.af = af
        self.afMax = afMax
        self.extreme = None
        self.trend = False
        self.curSAR = None
        self.nextSAR = None

        self.prevHigh = None
        self.prevLow = None

    def addData(self, low, close, high) -> None:
        # Start case, takes 2 iterations to setup
        if self.nextSAR is None:
            if self.prevLow is None:
                self.prevLow = close
                return

            # estimated downtrend
            if self.prevLow < close:
                self.trend = False
                self.extreme = low
            # else uptrend
            else:
                self.trend = True
                self.extreme = high

            self.nextSAR = (high + low) / 2
            self.prevLow = low
            self.prevHigh = high
            return

        # Update to today's SAR
        self.curSAR = self.nextSAR

        # Check for a trend switch
        if (self.trend and self.curSAR >= low) or (not self.trend and self.curSAR <= high):
            # Reverse the trend
            self.trend = not self.trend
            self.curSAR = self.extreme
            self.extreme = high if self.trend else low
            self.af = self.afStart

        # Check for new EP, inc AF if found
        if self.trend:
            if high > self.extreme:
                self.extreme = high
                self.af += AF_INC
        else:
            if low < self.extreme:
                self.extreme = low
                self.af += AF_INC

        # limit AF to max
        self.af = min(self.af, self.afMax)

        self.nextSAR = self.curSAR + self.af * (self.extreme - self.curSAR)

        # Limit nextSAR using ITS prev 2 lows and highs, i.e the current and 1 prev
        if self.trend:
            # uptrend, sar should be below prev 2 lows
            self.nextSAR = min(low, self.prevLow, self.nextSAR)
        else:
            # downtrend, sar should be above prev 2 highs
            self.nextSAR = max(high, self.prevHigh, self.nextSAR)

        # update prev vals
        self.prevLow = low
        self.prevHigh = high

    @ValueFunc(key='psar')
    def getSAR(self):
        return self.curSAR

    def setupTime(self) -> int:
        return 2
