import datetime
from configparser import ConfigParser
from typing import Dict
import os.path
import traceback
import colorama
import logging
import os
import time
import sys

from cash_money.trading.trader import Trader
from cash_money.trading.data.dataBroker import DataBroker
from cash_money.trading.data.yfinanceDataBroker import YFinanceDataBroker
from cash_money.trading.data.alpacaDataBroker import AlpacaDataBroker
from cash_money.trading.data.dataBroker import DataBroker
from ..trading.nodeStrategy import NodeStrategy
from .date_utils import calcSetupStartDate

logging.addLevelName(logging.WARNING, "WARN")

log = logging.getLogger("Run Utils")

_config = ConfigParser()
_systemLoaded = False

_CONFIG_PATH_KEY = "CM_CONFIG_DIR"

if _CONFIG_PATH_KEY in os.environ:
    CONFIG_DIR = os.environ[_CONFIG_PATH_KEY]
else:
    APP_DIR = os.path.split(os.path.dirname(sys.argv[0]))[0]
    CONFIG_DIR = os.path.join(APP_DIR, "config")

SYS_LOG_DIR = os.path.join(CONFIG_DIR, "logs", "system")
TRADE_LOGS_DIR = os.path.join(CONFIG_DIR, "logs", "trade")

_configLoc = os.path.join(CONFIG_DIR, "system.cfg")

_ERR_C = '\x1b[1;31m'
_DBG_C = '\x1b[1;32m'
_WRN_C = "\x1b[1;33m"
_END_C = '\x1b[0m'

_DATE_FMT = '%b-%d %H:%M:%S'
_DFLT = '{asctime} {levelname:5s} [{name:^15s}] {message}'
_FILE_FMT = logging.Formatter(_DFLT, datefmt=_DATE_FMT, style="{")

_DFLT_LOG_FMT = logging.Formatter(_DFLT, style="{", datefmt=_DATE_FMT)
_ERR_LOG_FMT = logging.Formatter(f"{_ERR_C}{_DFLT}{_END_C}", style="{", datefmt=_DATE_FMT)
_DBG_LOG_FMT = logging.Formatter(f"{_DBG_C}{_DFLT}{_END_C}", style="{", datefmt=_DATE_FMT)
_WRN_LOG_FMT = logging.Formatter(f"{_WRN_C}{_DFLT}{_END_C}", style="{", datefmt=_DATE_FMT)


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
        filehandler = logging.FileHandler(filename=f'{logDir}/{logname}.log', mode='w')
        filehandler.setLevel(level=loglevel)
        filehandler.setFormatter(_FILE_FMT)
        root.addHandler(filehandler)

    console1 = logging.StreamHandler(sys.stdout)
    console1.setLevel(loglevel)
    console1.setFormatter(_ConsoleFormatter())
    root.addHandler(console1)

    log.debug("Setup logging")

    # Disable logging for other libs
    others = [
        logging.getLogger("urllib3.connectionpool"),
        logging.getLogger("websockets.client"),
        logging.getLogger("asyncio"),
        logging.getLogger('matplotlib'),
        logging.getLogger('PIL'),
        logging.getLogger('yfinance'),
        logging.getLogger('peewee')
    ]

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
            raise RuntimeError(f"ERROR: Cannot find {_configLoc}")

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

        _setuplogging(loglevel, True, SYS_LOG_DIR)

        os.makedirs(TRADE_LOGS_DIR, exist_ok=True)

        #email_manager.setupEmailManager(syscfg)

    return _config


def loadDataBroker(config: ConfigParser) -> DataBroker:
    databrokerName = config["System"]["HistoricData"]

    match databrokerName.lower():
        case "yfinance":
            databroker = YFinanceDataBroker()
        case 'alpaca':
            databroker = AlpacaDataBroker(config["Alpaca"])

    return databroker


def setupStrategies(strats: Dict[str, NodeStrategy], targetDate: datetime.datetime, dataBroker: DataBroker):
    """
    Sets up the given strategies so that they are up to date with the target start day
    :param strats: The strats to set up
    :param targetDate: The date up to which the strategies should be run
    """

    setupTime = max([x.getSetupTime() for x in strats.values()])
    setupStart = calcSetupStartDate(targetDate - datetime.timedelta(1), setupTime)

    bars = dataBroker.getBars([sym for sym in strats], setupStart, targetDate)
    for sym, strat in strats.items():
        for bar in bars[sym]:
            if bar is not None:
                strat.addData(bar)
                strat.dryRun()

    log.info(f"Strategies setup with {setupTime} days")


def runTrader(trader: Trader):
    try:
        log.info("Trader init")
        trader.init()
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
