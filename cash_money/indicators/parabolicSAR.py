from cash_money.indicators.indicator import Indicator
from cash_money.objects.strategy_params import NumberParam
from .lineManager import LineManager

AF_INC = 0.02

_PSAR = 'PSAR'


class ParabolicSAR(Indicator):
    params = [NumberParam('af', "AF Start", float, 0.02),
              NumberParam('afMax', "AF Max", float, 0.2)]
    outputs = [_PSAR]

    def __init__(self, name: str, lineManager: LineManager, af: float = 0.02, afMax: float = 0.2):
        super().__init__(name)
        self._afStart = af
        self._af = af
        self._afMax = afMax
        self._extreme = None
        self._trend = False
        self.psar = lineManager.registerLine(name, _PSAR)
        self._nextSAR = None

        self._prevHigh = None
        self._prevLow = None

        self.hi, self.lo, self.close = lineManager.hlc()

    def update(self) -> None:
        # Start case, takes 2 iterations to setup
        if self._nextSAR is None:
            if self._prevLow is None:
                self._prevLow = self.close()
                return

            # estimated downtrend
            if self._prevLow < self.close():
                self._trend = False
                self._extreme = self.lo()
            # else uptrend
            else:
                self._trend = True
                self._extreme = self.hi()

            self._nextSAR = (self.hi() + self.lo()) / 2
            self._prevLow = self.lo()
            self._prevHigh = self.hi()
            return

        # Update to today's SAR
        todayPSAR = self._nextSAR

        # Check for a trend switch
        if (self._trend and todayPSAR >= self.lo()) or (not self._trend and todayPSAR <= self.hi()):
            # Reverse the trend
            self._trend = not self._trend
            todayPSAR = self._extreme
            self._extreme = self.hi() if self._trend else self.lo()
            self._af = self._afStart

        # Check for new EP, inc AF if found
        if self._trend:
            if self.hi() > self._extreme:
                self._extreme = self.hi()
                self._af += AF_INC
        else:
            if self.lo() < self._extreme:
                self._extreme = self.lo()
                self._af += AF_INC

        # limit AF to max
        self._af = min(self._af, self._afMax)

        # calc tomorrow's psar
        self._nextSAR = todayPSAR + self._af * (self._extreme - todayPSAR)

        # Limit tomorrow's psar using ITS prev 2 lows and highs, i.e today's and yesterday's lows
        if self._trend:
            # uptrend, sar should be below prev 2 lows
            self._nextSAR = min(self.lo(), self._prevLow, self._nextSAR)
        else:
            # downtrend, sar should be above prev 2 highs
            self._nextSAR = max(self.hi(), self._prevHigh, self._nextSAR)

        # Set output psar
        self.psar.add(todayPSAR)
        # update prev vals
        self._prevLow = self.lo()
        self._prevHigh = self.hi()

    def setupTime(self) -> int:
        return 2
