from abc import ABC
import datetime
from time import sleep

import alpaca.trading.models as models

import logging
from cash_money.cmErrors import CMError
from cash_money.utils.api_utils import CMAPI


def toTS(t):
    return t.replace(tzinfo=datetime.timezone.utc).timestamp()


tfLog = logging.getLogger("Timeframe")


class TimeFrame(ABC):

    def __init__(self, api: CMAPI):
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
            clock = self._api.trade.get_clock()
            if not isinstance(clock, models.Clock):
                raise CMError()

            diff = ts - toTS(clock.timestamp)
            if diff <= 0:
                return

            if diff > 6:
                # TODO add current time to log
                tfLog.info(f'Sleeping {diff / 60:.2f}min')
                timeToSleep = diff - 5
                sleep(timeToSleep)
            else:
                sleep(2)
