import time

from .timeframe import TimeFrame, toTS, tfLog
from cash_money.cmErrors import CMError
from cash_money.utils.api_utils import CMAPI

from alpaca.trading.models import Clock


class SecTF(TimeFrame):
    def __init__(self, api: CMAPI, secs: float):
        super().__init__(api)
        self.secs = secs
        self.notifySec = min(self.secs / 2, 600)

    def wait(self) -> None:
        clock = self._api.trade.get_clock()
        if not isinstance(clock, Clock):
            raise CMError()
        timeToClose = toTS(clock.next_close)
        timeToOpen = toTS(clock.next_open)
        now = toTS(clock.timestamp)

        if not clock.is_open or now + self.secs + 0.5 > timeToClose:
            # TODO add wait time
            tfLog.logInfo(f"Sleeping until market opens")
            self._waitForTS(timeToOpen + 1)
        else:
            tfLog.logInfo(f"Sleeping {self.secs}sec")
            time.sleep(self.secs)

    def notifyWait(self) -> None:
        tfLog.logInfo(f"Sending Notification in {self.notifySec:.1f}s")
        time.sleep(self.notifySec)

    def postWait(self) -> None:
        # ILB
        pass
