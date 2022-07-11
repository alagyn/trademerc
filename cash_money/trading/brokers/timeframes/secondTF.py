from .timeframe import TimeFrame, toTS, tfLog
import time
import alpaca_trade_api as alpaca

class SecTF(TimeFrame):
    def __init__(self, api: alpaca.REST, secs: float):
        super().__init__(api)
        self.secs = secs

    def wait(self) -> None:
        clock = self._api.get_clock()
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

    def notifyWait(self) -> float:
        return min(self.secs / 2, 600)

    def postWait(self) -> None:
        # ILB
        pass
