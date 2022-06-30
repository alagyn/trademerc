from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import OutPort, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.nodes.datakeys import CLOSE
from cash_money.stats.ema import EMA

_FP = "_FP"
_SP = "_SP"
_SigP = "_SGP"


class MACD(CMNode):
    """
    Moving Average Convergence Divergence
    """
    _OUTPUTS = [
        OutPort("MACD", FLOAT),
        OutPort("Signal", FLOAT)
    ]
    _ARGS = [
        NodeArg(_FP, INT, "Fast Period", 5),
        NodeArg(_SP, INT, "Slow Period", 10),
        NodeArg(_SigP, INT, "Signal Period", 10)
    ]
    NODETYPE = "MACD"

    def __init__(self):
        super().__init__()
        self._fp = self.args[_FP]
        self._sp = self.args[_SP]
        self._sigP = self.args[_SigP]

        self._fastEMA = None
        self._slowEMA = None
        self._sigEMA = None

        self.macdOut = self.outputs[0]
        self.signalOut = self.outputs[1]

    def setup(self) -> None:
        self._fastEMA = EMA(period=self._fp.value)
        self._slowEMA = EMA(period=self._sp.value)
        self._sigEMA = EMA(period=self._sigP.value)

    def execute(self) -> None:
        close = self.datamap[CLOSE]
        fastVal = self._fastEMA.next(close)
        slowVal = self._slowEMA.next(close)

        newMACD = fastVal - slowVal
        signal = self._sigEMA.next(newMACD)

        self.macdOut.setValue(newMACD)
        self.signalOut.setValue(signal)

    def setupTime(self) -> int:
        return max(self._fp.value, self._sp.value, self._sigP.value)
