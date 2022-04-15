import datetime
from typing import Dict, Optional, List, Tuple

import yfinance as yf

from consts import DATE_FMT
from objects.bar import Bar
from strategies.strategy import Strategy
from trading.brokers.broker import Broker
from trading.cm_trader import Trader

import logging as log


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
        b = yf.download(sym, startstr, endstr)
        bars = [Bar(b['Low'][x], b['Close'][x], b['High'][x], b.index[x]) for x in range(len(b))]

        allBars[sym] = bars

        strat.setupIndicators(bars[0:setupTime])

    log.info(f"Setup: Strategies setup with {setupTime} days")

    return allBars, setupTime


def runTradeBroker(trader: Trader, broker: Broker):
    log.info("Run: Broker Pre-run")
    broker.preRun()

    log.info("Run: Starting Loop")
    while True:
        if not broker.preTrade():
            break

        trader.trade()
        broker.postTrade()
        broker.incDay()

    log.info("Run: Broker Post-run")
    broker.postRun()
    log.info("Run: Run Complete")
