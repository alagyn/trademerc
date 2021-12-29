from indicators.indicator import Indicator, HIGH_PRIORITY

AF_INC = 0.02


class ParabolicSAR(Indicator):
    def __init__(self, af: float = 0.02, afMax: float = 0.2):
        super().__init__(HIGH_PRIORITY, {'psar': self.getSAR})

        self.afStart = af
        self.af = af
        self.afMax = afMax
        self.extreme = None
        self.trend = False
        self.curSAR = None
        self.nextSAR = None

        self.prevHigh = None
        self.prevLow = None

    def addData(self, *, low=None, close=None, high=None) -> None:
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
            if self.nextSAR > low or self.nextSAR > self.prevLow:
                self.nextSAR = min(low, self.prevLow)
        else:
            if self.nextSAR < high or self.nextSAR < self.prevHigh:
                self.nextSAR = max(high, self.prevHigh)

        # update prev vals
        self.prevLow = low
        self.prevHigh = high

    def getSAR(self):
        return self.curSAR

    def setupTime(self) -> int:
        return 2


if __name__ == '__main__':
    sar = ParabolicSAR()

    testvals = [
        (47.85, 47.48),
        (47.83, 47.55),
        (47.95, 47.32),
        (48.11, 47.25),
        (48.30, 47.77),
        (48.17, 47.91),
        (48.60, 47.90),
        (48.33, 47.74),
        (48.40, 48.10),
        (48.55, 48.06),
        (48.45, 48.07),
        (48.70, 47.79),
        (48.72, 48.14),
        (48.90, 48.39),
        (48.87, 48.37),
        (49.05, 48.64),
        (49.20, 48.94),
        (49.35, 48.86)
    ]

    for x in testvals:
        sar.addData(low=x[1], high=x[0], close=(x[0] + x[1]) / 2)
        if sar.getSAR() is not None:
            print(f'H:{x[0]:.2f} L:{x[1]:.2f} SAR:{sar.getSAR():.2f}')
