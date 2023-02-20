from abc import ABC
import datetime
from time import sleep

from alpaca.trading.client import TradingClient
import alpaca.trading.models as models

from cash_money.utils.log_utils import CMLogger
from cash_money.cmErrors import CMError


def toTS(t):
    return t.replace(tzinfo=datetime.timezone.utc).timestamp()


tfLog = CMLogger("Timeframe")


class TimeFrame(ABC):
    def __init__(self, api: TradingClient):
        self._api = api

    def wait(self) -> None:
        raise NotImplementedError

    def notifyWait(self) -> float:
        raise NotImplementedError

    def postWait(self) -> None:
        raise NotImplementedError

    def _waitForTS(self, ts):
        """Utility to wait until timestamp"""

        while True:
            clock = self._api.get_clock()
            if not isinstance(clock, models.Clock):
                raise CMError()

            diff = ts - toTS(clock.timestamp)
            if diff <= 0:
                return

            if diff > 6:
                # TODO add current time to log
                tfLog.logInfo(f'Sleeping {diff / 60:.2f}min')
                timeToSleep = diff - 5
                sleep(timeToSleep)
            else:
                sleep(2)
