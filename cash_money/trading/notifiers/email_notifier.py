import requests
from threading import Thread
import time
import datetime
import logging
import smtplib
import os
import time
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader, select_autoescape

from cash_money.trading.events import EndOfTradeStepEvent, ErrorEvent

from ..events import CMEventListener, Notification

log = logging.getLogger("Email")


class NotifyKeys:

    class Portfolio:
        START = "portfolio_start"
        CUR = "portfolio_cur"
        PL = "portfolio_pl"

    TRADES = "trades"

    class Trade:
        Symbol = "symbol"
        Side = "side"
        Qty = "qty"
        Price = "price"
        Value = "value"

    POSITIONS = "positions"

    class Position:
        Symbol = "symbol"
        Qty = "qty"
        PL = "pl"
        Price = "price"
        Value = "value"
        PurchaseValue = "p_value"
        PurchaseDate = "p_date"
        StopPrice = "stop_price"
        LastStop = "last_stop"
        NextStop = "next_stop"


class EmailNotifier(CMEventListener):

    def __init__(self, config) -> None:
        self._recievingEmail = config['Email']['receiving_email']
        self._sendingEmail = config['Email']['sending_email']
        self._sendingPass = config['Email']['sending_email_pass']
        self._smtpServer = config['Email']['smtp_server']
        self._smtpPort = config['Email']['smtp_port']

        self.htmlEnv = Environment(loader=FileSystemLoader('html-templates'), autoescape=select_autoescape())
        self.emailTemplate = self.htmlEnv.get_template("emailtemplate.html")

    def _updateThread(self, n: Notification):
        args = {
            NotifyKeys.Portfolio.START: format(n.equity_prev, ".2f"),
            NotifyKeys.Portfolio.CUR: format(n.equity_cur, ".2f"),
            NotifyKeys.Portfolio.PL: format(n.equity_pl, ".2f"),
            NotifyKeys.TRADES: n.trades,
            NotifyKeys.POSITIONS: n.positions
        }
        txt = self.emailTemplate.render(**args)

        self.send_message(txt)

    def send_message(self, msg: str, title: str | None = None):
        now = time.time()

        if title is None:
            title = datetime.datetime.now().strftime("Trades %a-%b-%d-%Y-%H.%M.%S")

        email = MIMEText(msg, "html")
        email["Subject"] = title
        try:
            with smtplib.SMTP_SSL(self._smtpServer, self._smtpPort) as serv:
                serv.login(self._sendingEmail, self._sendingPass)
                serv.sendmail(self._sendingEmail, self._recievingEmail, email.as_string())
        except Exception as e:
            log.error("Failed to send email: {}", e)

    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        Thread(target=self._updateThread, args=(event.notif, ), daemon=True).start()

    def onError(self, event: ErrorEvent):
        self.send_message(event.message, "Error")


if __name__ == "__main__":
    from cash_money.utils import run_utils

    import sys
    print(sys.argv[0])

    cfg = run_utils.loadSystem()
    notif = EmailNotifier(cfg)
    n = Notification(datetime.datetime.now())
    n.addTrade("QQQ", "BUY", 25, 1.25, 500)
    n.addTrade("AAA", "BUY", 25, 1.25, 500)
    n.addTrade("BBB", "BUY", 25, 1.25, 500)
    n.addPosition("QQQ", 25, 0.15, 6.90, 250, 2.3, 1.2)
    notif._updateThread(n)
