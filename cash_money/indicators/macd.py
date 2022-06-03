from cash_money.indicators.indicator import Indicator
from cash_money.objects.strategy_params import NumberParam
from cash_money.indicators.ema import SoloEMA
from .lineManager import LineManager, CLOSE

_MACD = 'MACD'
_SIGNAL = 'Signal'


class MACD(Indicator):
    """
    Moving Average Convergence Divergence
    """

    params = [NumberParam('fastPeriod', "Fast Period", int, 5),
              NumberParam('slowPeriod', "Slow Period", int, 10),
              NumberParam('sigPeriod', "Signal Period", int, 10)]
    outputs = [_MACD, _SIGNAL]

    def __init__(self, name: str, lineManager: LineManager, fastPeriod: int, slowPeriod: int, sigPeriod: int):
        super().__init__(name)
        self._fp = fastPeriod
        self._sp = slowPeriod
        self._sigP = sigPeriod

        self._fastEMA = SoloEMA(period=fastPeriod)
        self._slowEMA = SoloEMA(period=slowPeriod)
        self._sigEMA = SoloEMA(period=sigPeriod)

        self.macd = lineManager.registerLine(name, _MACD)
        self.signal = lineManager.registerLine(name, _SIGNAL)

        self.close = lineManager.requestInput(CLOSE)

    def update(self) -> None:
        self._fastEMA.next(self.close())
        self._slowEMA.next(self.close())

        fastVal = self._fastEMA.getValue()
        slowVal = self._slowEMA.getValue()

        newMACD = fastVal - slowVal
        self.macd.add(newMACD)

        newSignal = self._sigEMA.next(newMACD)
        self.signal.add(newSignal)

    def setupTime(self) -> int:
        return max(self._fp, self._sp, self._sigP)
