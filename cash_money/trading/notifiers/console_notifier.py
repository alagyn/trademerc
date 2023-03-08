from .notifier import Notifier
from cash_money.utils.log_utils import CMLogger
from cash_money.utils.tumble import Tumble, Column, FloatColumn

log = CMLogger("Notify")

TRADE_COLS = [
    Column("Symbol", 4, "s"),
    Column("Side", 4, "s"),
    Column("Qty", 5, "d"),
    FloatColumn("Price", 5, 2),
    FloatColumn("Value", 5, 2)
]

POSIT_COLS = [
    Column("Symbol", 4, "s"),
    Column("Qty", 5, "d"),
    FloatColumn("PL", 5, 2),
    FloatColumn("Cur Price", 5, 2),
    FloatColumn("Value", 5, 2),
    FloatColumn("Stop Price", 5, 2)
]


class ConsoleNotifier(Notifier):
    def __init__(self) -> None:
        self._trade_tumble = Tumble(TRADE_COLS)
        self._pos_tumble = Tumble(POSIT_COLS)

    def update(self, n):
        log.logInfo(f'Portfolio Start: ${n.portfolio_start:.2f}')
        log.logInfo(f'Portfolio Cur: ${n.portfolio_cur:.2f}')
        log.logInfo(f'Portfolio P/L: ${n.portfolio_pl:.2f}')

        msg = ["Update"]
        if len(n.trades) > 0:
            msg.append("Trades:")
            msg.append(self._trade_tumble.header())
            for x in n.trades:
                msg.append(
                    self._trade_tumble.row(
                        x.symbol,
                        x.side,
                        x.qty,
                        x.price,
                        x.value)
                )
        else:
            msg.append("No Trades")

        if len(n.positions) > 0:
            msg.append("\nPositions:")
            msg.append(self._pos_tumble.header())
            for x in n.positions:
                msg.append(
                    self._pos_tumble.row(
                        x.symbol,
                        x.qty,
                        x.pl,
                        x.price,
                        x.value,
                        x.stopPrice
                    )
                )
            msg.append("")

        log.logInfo("\n".join(msg))
