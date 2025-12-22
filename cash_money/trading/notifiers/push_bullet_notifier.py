import requests
from threading import Thread
import time
import datetime
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape

from cash_money.trading.events import EndOfTradeStepEvent

from ..events import CMEventListener, Notification

log = logging.getLogger("PushBullet")

ENDPOINT = "https://api.pushbullet.com"


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


class PushBulletNotifier(CMEventListener):

    def __init__(self, config) -> None:
        self._token = config['PushBullet']['API_KEY']

        self.htmlEnv = Environment(loader=FileSystemLoader('html-templates'), autoescape=select_autoescape())
        self.emailTemplate = self.htmlEnv.get_template("emailtemplate.html")

    def _updateThread(self, n: Notification):
        args = {
            NotifyKeys.Portfolio.START: n.equity_prev,
            NotifyKeys.Portfolio.CUR: n.equity_cur,
            NotifyKeys.Portfolio.PL: n.equity_pl,
            NotifyKeys.TRADES: n.trades,
            NotifyKeys.POSITIONS: n.positions
        }
        txt = self.emailTemplate.render(**args)

        self.send_message(txt)

    def send_message(self, msg: str):
        now = time.time()

        title = datetime.datetime.now().strftime("Trades-%a-%b-%d-%Y-%H.%M.%S")

        uploadRequestData = {
            "file_name": f'{title}.html',
            "file_type": "text/html"
        }

        headers = {
            "Access-Token": self._token
        }

        print("requesting upload")
        res = requests.post(
            f'{ENDPOINT}/v2/upload-request',
            headers=headers,
            data=uploadRequestData,
        )

        try:
            resData = res.json()
        except:
            log.error(f"Upload request failed, {res}")
            return

        # upload the file
        print("uploading file")
        res = requests.post(
            resData["upload_url"], files={
                "file": (
                    resData["file_name"],
                    msg.encode(),
                    resData["file_type"],
                )
            }
        )

        if res.status_code != 204:
            try:
                errorData = res.json()
            except:
                errorData = None
            log.error(f"Upload failed, {res.status_code}, {errorData}")
            return

        data = {
            "type": "file",
            "title": title,
            "file_name": resData["file_name"],
            "file_url": resData["file_url"],
            "file_type": resData["file_type"]
        }
        print("posting push")
        res = requests.post(
            f'{ENDPOINT}/v2/pushes', headers={
                'Access-Token': self._token
            }, data=data, timeout=10
        )

        if res.status_code != 200:
            log.error(f"Push failed, {res.status_code}, {res.json()}")
            return

    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        Thread(target=self._updateThread, args=(event.notif, ), daemon=True).start()


if __name__ == "__main__":
    from cash_money.utils import run_utils

    import sys
    print(sys.argv[0])

    cfg = run_utils.loadSystem()
    notif = PushBulletNotifier(cfg)
    n = Notification(datetime.datetime.now())
    n.addTrade("QQQ", "BUY", 25, 1.25, 500)
    n.addTrade("AAA", "BUY", 25, 1.25, 500)
    n.addTrade("BBB", "BUY", 25, 1.25, 500)
    n.addPosition("QQQ", 25, 0.15, 6.90, 250, 2.3, 1.2)
    notif._updateThread(n)
