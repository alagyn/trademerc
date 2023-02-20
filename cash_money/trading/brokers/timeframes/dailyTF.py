from .timeframe import TimeFrame, tfLog, toTS

from alpaca.trading.client import TradingClient


class DailyTF(TimeFrame):
    def __init__(self, api: TradingClient, anchor: str, minoffset: float):
        super(DailyTF, self).__init__(api)
        if anchor == "open":
            self.anchorStart = True
        elif anchor == "close":
            self.anchorStart = False
        else:
            raise RuntimeError(f"Invalid anchor: {anchor}")

        self._secs = minoffset * 60
        self._min = f"{minoffset:.2f}min"

    def wait(self):
        clock = self._api.get_clock()

        if self.anchorStart:
            tfLog.logInfo(f"Sleeping until {self._min} after Open")
            timeToOpen = toTS(clock.next_open)
            self._waitForTS(timeToOpen + self._secs)
        else:
            tfLog.logInfo(f"Sleeping until {self._min} before close")
            timeToClose = toTS(clock.next_close)
            self._waitForTS(timeToClose - self._secs)

    def postWait(self) -> None:
        clock = self._api.get_clock()

        tfLog.logInfo(f'Forcing sleep until open')
        timeToOpen = toTS(clock.next_open)
        self._waitForTS(timeToOpen)

    def notifyWait(self) -> float:
        return 600
