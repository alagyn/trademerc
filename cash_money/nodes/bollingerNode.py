from nodepasta.argtypes import FLOAT, INT
from nodepasta.node import Port, NodeArg

from cash_money.nodes.cmNode import CMNode
from cash_money.stats.sma import SMA

_Period = '_period'
_StdDev = '_stddev'


class BollingerNode(CMNode):
    """
    Bollinger Bands
    """
    DESCRIPTION = 'Calculates Bollinger bands'
    _INPUTS = [
        Port("Input", FLOAT, "The input value")
    ]
    _OUTPUTS = [
        Port("Top", FLOAT, "The top band"),
        Port("Bottom", FLOAT, "The bottom band"),
        Port("Width", FLOAT, "The Distance between bands"),
        Port("Center", FLOAT, "The Center Simple-Moving-Avg"),
        Port("Std Dev", FLOAT, "The Standard Deviation")
    ]
    _ARGS = [
        NodeArg(_Period, INT, 'Period', 'The period of the center SMA', 20),
        NodeArg(_StdDev, FLOAT, 'Std Devs',
                'The number of standard deviations to use', 2)
    ]
    NODETYPE = 'Bollinger Bands'

    def init(self):
        self._period = self.args[_Period]
        self._stdDev = self.args[_StdDev]
        self._sma = SMA(period=self._period.value)

        self._in = self.inputs[0]

        self._topOut = self.outputs[0]
        self._botOut = self.outputs[1]
        self._widthOut = self.outputs[2]
        self._centerOut = self.outputs[3]
        self._sdOut = self.outputs[4]

    def setup(self) -> None:
        self._sma = SMA(period=self._period.value)

    def execute(self) -> None:
        # Get the next SMA value
        val = self._sma.next(self._in.value())
        self._centerOut.value(val)
        # Get the Std Dev
        SD = self._sma.std_dev()
        self._sdOut.value(SD)
        # Get the band distance
        band = self._stdDev.value * SD
        self._topOut.value(val + band)
        self._botOut.value(val - band)
        self._widthOut.value(band * 2)

    def setupTime(self) -> int:
        return self._period.value
