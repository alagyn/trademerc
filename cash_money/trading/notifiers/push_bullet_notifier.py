import requests
from threading import Thread

from cash_money.trading.events import EndOfTradeStepEvent

from ..events import CMEventListener, Notification
from cash_money.utils.tumble import Tumble, Column, FloatColumn


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

ENDPOINT = "https://api.pushbullet.com"

class PushBulletNotifier(CMEventListener):
    def __init__(self, config) -> None:
        self._token = config['PushBullet']['API_KEY']
        self._trade_tumble = Tumble(TRADE_COLS)
        self._pos_tumble = Tumble(POSIT_COLS)

    def _updateThread(self, n: Notification):
        title = "Trade Update"
        msg = []
        msg.append(f'Cash: ${n.cash:.2f}')
        msg.append(
            f"Equity: ${n.equity_prev:.2f} -> ${n.equity_cur:.2f}, P/L: ${n.equity_pl:.2f}"
        )
        if len(n.trades) > 0:
            msg.append("Trades:")
            msg.append(self._trade_tumble.header())
            msg.append(self._trade_tumble.breaker())
            for x in n.trades:
                msg.append(
                    self._trade_tumble.row(
                        x.symbol, x.side, x.qty, x.price, x.value
                    )
                )
        else:
            msg.append("No Trades")

        if len(n.positions) > 0:
            msg.append("Positions:")
            msg.append(self._pos_tumble.header())
            msg.append(self._pos_tumble.breaker())
            for x in n.positions:
                msg.append(
                    self._pos_tumble.row(
                        x.symbol, x.qty, x.pl, x.price, x.value, x.stopPrice
                    )
                )
            msg.append("")
        else:
            msg.append("No Open Positions")

        txt = '\n'.join(msg)

        data = {
            "type": "note",
            "title": title,
            "body": txt
        }

        requests.post(f'{ENDPOINT}/v2/pushes', headers={'Access-Token': self._token}, data=data, timeout=10)

    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        Thread(target=self._updateThread, args=(event.notif,), daemon=True).start()
