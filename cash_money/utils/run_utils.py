import datetime
from configparser import ConfigParser
from typing import Dict, Optional, List, Tuple
from sys import exit
import os.path
import traceback
import colorama
import tkinter.messagebox as dialog
import logging
import os
import time
import sys

import yfinance as yf
import pandas as pd

from cash_money.consts import DATE_FMT
from cash_money.objects import Bar
from cash_money.trading.trader import Trader
from ..trading.nodeStrategy import NodeStrategy
from .date_utils import nextBusinessDay, calcSetupStartDate

logging.addLevelName(logging.WARNING, "WARN")

log = logging.getLogger("Run Utils")

_config = ConfigParser()
_systemLoaded = False

_configLoc = r"config/system.cfg"

_ERR_C = '\x1b[1;31m'
_DBG_C = '\x1b[1;32m'
_WRN_C = "\x1b[1;33m"
_END_C = '\x1b[0m'

_DFLT = '{levelname:5s} [{name:^15s}] {message}'
_FILE_FMT = logging.Formatter(
    f'{{asctime}} {_DFLT}', datefmt='%b-%d %H:%M:%S', style="{"
)

_DFLT_LOG_FMT = logging.Formatter(_DFLT, style="{")
_ERR_LOG_FMT = logging.Formatter(f"{_ERR_C}{_DFLT}{_END_C}", style="{")
_DBG_LOG_FMT = logging.Formatter(f"{_DBG_C}{_DFLT}{_END_C}", style="{")
_WRN_LOG_FMT = logging.Formatter(f"{_WRN_C}{_DFLT}{_END_C}", style="{")


class _ConsoleFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        if record.levelno == logging.DEBUG:
            return _DBG_LOG_FMT.format(record)
        elif record.levelno == logging.WARNING:
            return _WRN_LOG_FMT.format(record)
        elif record.levelno == logging.ERROR:
            return _ERR_LOG_FMT.format(record)
        else:
            return _DFLT_LOG_FMT.format(record)


def _setuplogging(loglevel: int, logToFile: bool, logDir: str):

    root = logging.getLogger()
    root.setLevel(loglevel)

    if logToFile:
        logname = time.strftime(r'%Y_%b_%dT%H_%M_%S')

        os.makedirs(logDir, exist_ok=True)

        # Terminal Log File
        filehandler = logging.FileHandler(
            filename=f'{logDir}/{logname}.log', mode='w'
        )
        filehandler.setLevel(level=loglevel)
        filehandler.setFormatter(_FILE_FMT)
        root.addHandler(filehandler)

    console1 = logging.StreamHandler(sys.stdout)
    console1.setLevel(loglevel)
    console1.setFormatter(_ConsoleFormatter())
    root.addHandler(console1)

    log.debug("Setup logging")

    # Disable logging for other libs
    others = [logging.getLogger("urllib3.connectionpool"), logging.getLogger("websockets.client"), logging.getLogger("asyncio")]

    for x in others:
        log.debug("Disabling logs for %s", x.name)
        x.setLevel(logging.WARN)


def loadSystem() -> ConfigParser:
    global _systemLoaded, _config

    if not _systemLoaded:
        colorama.init()
        _systemLoaded = True
        if os.path.exists(_configLoc):
            _config.read(_configLoc)
        else:
            print(f"ERROR: Cannot find {_configLoc}")
            dialog.showerror(
                "Error: Cash Money", f"Cannot find \"{_configLoc}\""
            )
            exit(1)

        syscfg = _config['System']

        loglevelStr = syscfg["LogLevel"].strip().lower()
        if loglevelStr.startswith('d'):
            loglevel = logging.DEBUG
        elif loglevelStr.startswith("i"):
            loglevel = logging.INFO
        elif loglevelStr.startswith("w"):
            loglevel = logging.WARN
        elif loglevelStr.startswith('e'):
            loglevel = logging.ERROR
        else:
            loglevel = logging.INFO

        _setuplogging(
            loglevel, syscfg.getboolean('LogToFile'), syscfg['LogDirectory']
        )

    return _config


def parseYFDate(d: pd.Timestamp) -> datetime.date:
    return d.to_pydatetime().date()


class BarEntry:

    def __init__(self, bar: Optional[Bar], date: datetime.date) -> None:
        self.bar = bar
        self.date = date


BarDict = Dict[str, List[BarEntry]]


def downloadDailyBars(
    symbols: List[str], startDate: datetime.date, endDate: datetime.date
) -> BarDict:
    startStr = startDate.strftime(DATE_FMT)
    endStr = endDate.strftime(DATE_FMT)

    dirtyBars: Dict[str, List[BarEntry]] = {}
    for sym in symbols:
        b = yf.download(sym, startStr, endStr, progress=False)
        bars = [
            BarEntry(
                Bar(
                    b['Low'][x],
                    b['Close'][x],
                    b['High'][x],
                    b['Volume'][x],
                ),
                parseYFDate(b.index[x]) # type: ignore
            ) for x in range(len(b))
        ]

        dirtyBars[sym] = bars

    # Normalize all the bars
    # Make the lists of bars have the same date at every index
    # Bar entries won't have a bar if there was no data for that day
    cleanBarsDict: BarDict = {sym: list()
                              for sym in symbols}
    curDate = min([x[0].date for x in dirtyBars.values()])

    # Dict of current indices for each symbol
    idxs = {sym: 0
            for sym in symbols}

    # We want to do them all at once so we can filter out holidays and
    # stuff by checking if every bar is none for a particular day
    while curDate <= endDate:
        # check if we have at least one bar for this day
        haveBar = False
        for sym, idx in list(idxs.items()):
            bars = dirtyBars[sym]
            if idx >= len(bars):
                continue
            bar = bars[idx]
            if bar.date == curDate:
                cleanBarsDict[sym].append(bar)
                haveBar = True
                idxs[sym] += 1
            else:
                cleanBarsDict[sym].append(BarEntry(None, curDate))

        # If we don't have any bars for this date (probably a holiday)
        if not haveBar:
            # Then we have a row of empty BarEntries
            for sym in idxs:
                # Remove them
                cleanBarsDict[sym].pop()

        # Go to next business day
        curDate = nextBusinessDay(curDate)

    return cleanBarsDict


def setupStrategies(
    strats: Dict[str, NodeStrategy], targetDate: datetime.date
):
    """
    Sets up the given strategies so that they are up to date with the target start day
    :param strats: The strats to set up
    :param targetDate: The date up to which the strategies should be run
    """

    setupTime = max([x.getSetupTime() for x in strats.values()])
    setupStart = calcSetupStartDate(
        targetDate - datetime.timedelta(1), setupTime
    )

    bars = downloadDailyBars([sym for sym in strats], setupStart, targetDate)
    for sym, strat in strats.items():
        for bar in bars[sym]:
            if bar.bar is not None:
                strat.addData(bar.bar)
                strat.dryRun()

    log.info(f"Strategies setup with {setupTime} days")


def runTrader(trader: Trader):
    try:
        log.info("Trader Pre-run")
        trader.preRun()

        log.info("Starting Loop")
        while True:
            if not trader.preTrade():
                break

            trader.trade()
            trader.postTrade()
            trader.incStep()

        log.info("Trader Post-run")
        trader.postRun()
        log.info("Run Complete")
    except Exception as err:
        # Catch errors to log them to file
        tb = traceback.TracebackException.from_exception(err).format()
        tb = "".join(tb)
        msg = f'ERROR:\n{tb}'
        log.error(msg)
        # raise to propagate
        raise


def showError(title: str, message: str) -> None:
    dialog.showerror(title, message)
