from ..events import CMEventListener, Notification, EndOfTradeStepEvent
from cash_money.utils.tumble import Tumble, Column, FloatColumn

TRADE_COLS = [
    Column("Symbol", 4, "s"),
    Column("Side", 4, "s"),
    FloatColumn("Qty", 5, 2),
    FloatColumn("Price", 5, 2),
    FloatColumn("Value", 5, 2)
]

POSIT_COLS = [
    Column("Symbol", 4, "s"),
    FloatColumn("Qty", 5, 2),
    FloatColumn("PL", 5, 2),
    FloatColumn("Cur Price", 5, 2),
    FloatColumn("Value", 5, 2),
    FloatColumn("Stop Price", 5, 2)
]


class PlainTextFormatter(CMEventListener):

    def __init__(self) -> None:
        self._trade_tumble = Tumble(TRADE_COLS)
        self._pos_tumble = Tumble(POSIT_COLS)

    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        n = event.notif
        msg = [f'Trade Step {event.notif.date}']
        msg.append(f'Cash: ${n.cash:.2f}')
        msg.append(f"Equity: ${n.equity_prev:.2f} -> ${n.equity_cur:.2f}, P/L: ${n.equity_pl:.2f}")
        if len(n.trades) > 0:
            msg.append("Trades:")
            msg.append(self._trade_tumble.header())
            msg.append(self._trade_tumble.breaker())
            for x in n.trades:
                msg.append(self._trade_tumble.row(x.symbol, x.side, x.qty, x.price, x.value))
        else:
            msg.append("No Trades")

        if len(n.positions) > 0:
            msg.append("Positions:")
            msg.append(self._pos_tumble.header())
            msg.append(self._pos_tumble.breaker())
            for x in n.positions:
                msg.append(self._pos_tumble.row(x.symbol, x.qty, x.pl, x.price, x.value, x.stopPrice))
            msg.append("")
        else:
            msg.append("No Open Positions\n")

        self.write(msg)

    def write(self, lines: list[str]) -> None:
        raise NotImplementedError()


class PlainTextNotifier(PlainTextFormatter):

    def __init__(self, outputFile: str) -> None:
        super().__init__()

        self.f = open(outputFile, mode='w')

    def __del__(self):
        try:
            self.f.close()
        except:
            pass

    def write(self, lines: list[str]) -> None:
        self.f.write("\n".join(lines))
        self.f.write("\n------------------------------------------------------------\n")
