import datetime
from configparser import ConfigParser
from typing import Dict, Optional, List, Tuple

import yfinance as yf

from consts import DATE_FMT
from objects.bar import Bar
from strategies.strategy import Strategy
from trading.brokers.broker import Broker
from trading.cm_trader import Trader
from .log_utils import _setupLogger, logInfo

_config = None
_systemLoaded = False

def loadSystem() -> ConfigParser:
    global _systemLoaded, _config

    if not _systemLoaded:
        _systemLoaded = True
        _config = ConfigParser()
        _config.read(r'config/system.cfg')

        syscfg = _config['System']

        _setupLogger(
            syscfg.getboolean('DEBUG'),
            syscfg.getboolean('LogToFile'),
            syscfg['LogDirectory'])

    return _config


def calcSetupStartDate(endDay: datetime.datetime, setupTime):
    out = endDay
    while out.weekday() >= 5:
        out -= datetime.timedelta(1)

    while setupTime >= 0 or out.weekday() >= 5:
        out -= datetime.timedelta(1)
        if out.weekday() < 5:
            setupTime -= 1

    return out

def setupStrategies(strats: Dict[str, Strategy], afterSetupDate: datetime.datetime,
                    endDate: Optional[datetime.datetime] = None) -> Tuple[Dict[str, List[Bar]], int]:
    """
    Sets up the given strategies so that they are up to date with the
    passed afterSetupDate
    :param strats: The strats to set up
    :param afterSetupDate: The date up to which the strategies should be run
    :param endDate: Optional, The date up to which bars should be retrieved
    :return: All the retrieved bars and the number of days used to setup
    """

    setupTime = max([x.getSetupTime() for x in strats.values()])
    setupStart = calcSetupStartDate(afterSetupDate - datetime.timedelta(1), setupTime)

    startstr = setupStart.strftime(DATE_FMT)
    if endDate is None:
        endstr = afterSetupDate.strftime(DATE_FMT)
    else:
        endstr = endDate.strftime(DATE_FMT)

    allBars = {}
    for sym, strat in strats.items():
        b = yf.download(sym, startstr, endstr, progress=False)
        bars = [Bar(b['Low'][x], b['Close'][x], b['High'][x], b.index[x]) for x in range(len(b))]

        allBars[sym] = bars

        strat.setupIndicators(bars[0:setupTime])

    logInfo("Setup", f"Strategies setup with {setupTime} days")

    return allBars, setupTime


def runTradeBroker(trader: Trader, broker: Broker):
    logInfo("Run", "Broker Pre-run")
    broker.preRun()

    logInfo("Run", "Starting Loop")
    while True:
        if not broker.preTrade():
            break

        trader.trade()
        broker.postTrade()
        broker.incDay()

    logInfo("Run", "Broker Post-run")
    broker.postRun()
    logInfo("Run", "Run Complete")
