import datetime
from configparser import ConfigParser
from typing import Dict, Optional, List, Tuple
import os.path

import yfinance as yf

from cash_money.consts import DATE_FMT
from cash_money.objects.bar import Bar
from cash_money.trading.brokers.broker import Broker
from cash_money.trading.cm_trader import Trader
from .log_utils import _setupLogger, CMLogger
from ..trading.nodeStrategy import NodeStrategy

_config = None
_systemLoaded = False

_configLoc = r"config/system.cfg"

log = CMLogger("Run Utils")

def loadSystem() -> ConfigParser:
    global _systemLoaded, _config

    if not _systemLoaded:
        _systemLoaded = True
        _config = ConfigParser()
        if os.path.exists(_configLoc):
            _config.read(_configLoc)
        else:
            print(f"ERROR: Cannot find {_configLoc}")
            exit(1)

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

def setupStrategies(strats: Dict[str, NodeStrategy], afterSetupDate: datetime.datetime,
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
        bars = [Bar(b['Low'][x], b['Close'][x], b['High'][x], b['Volume'][x], b.index[x]) for x in range(len(b))]

        allBars[sym] = bars

        for x in bars[0:setupTime]:
            strat.addData(x)

    log.logInfo(f"Strategies setup with {setupTime} days")

    return allBars, setupTime


def runTradeBroker(trader: Trader, broker: Broker):
    log.logInfo("Broker Pre-run")
    broker.preRun()

    log.logInfo("Starting Loop")
    while True:
        if not broker.preTrade():
            break

        trader.trade()
        broker.postTrade()
        broker.incDay()

    log.logInfo("Broker Post-run")
    broker.postRun()
    log.logInfo("Run Complete")
