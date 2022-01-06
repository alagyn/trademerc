import logging as log
import datetime
from typing import List
from configparser import ConfigParser

from consts import DATE_FMT, LIVE_ENDPOINT, PAPER_ENDPOINT
from objects.stock import Stock
import cmErrors

import alpaca_trade_api as alpaca
from alpaca_trade_api.common import URL
from alpaca_trade_api import TimeFrame, TimeFrameUnit


def loadPaperAPI(apiCfg=None):
    if apiCfg is None:
        apiCfg = ConfigParser()
        apiCfg.read('config/system.cfg')
        apiCfg = apiCfg['Alpaca']

    log.info('Initializing Paper Account')
    api_key = str(apiCfg['Paper_API_Key'])
    api_secret = str(apiCfg['Paper_API_Secret'])
    endpoint = PAPER_ENDPOINT
    return alpaca.REST(api_key, api_secret, URL(endpoint), 'v2')


def loadLiveAPI(apiCfg=None):
    log.info('Initializing Live Account')
    api_key = apiCfg['Live_API_Key']
    api_secret = apiCfg['Live_API_Secret']
    endpoint = LIVE_ENDPOINT
    return alpaca.REST(api_key, api_secret, URL(endpoint), 'v2')


def loadAPI(apiCfg, liveRun: bool = False):
    if liveRun:
        x = input('Are you sure you want to run using the LIVE ACCOUNT? (YES/NO):')
        if x != 'YES':
            return None
        else:
            return loadLiveAPI(apiCfg)

    return loadPaperAPI()


def calcSetupStartDate(endDay: datetime.datetime, setupTime):
    out = endDay
    while out.weekday() >= 5:
        out -= datetime.timedelta(1)

    while setupTime >= 0 or out.weekday() >= 5:
        out -= datetime.timedelta(1)
        if out.weekday() < 5:
            setupTime -= 1

    return out


def getBars(api: alpaca.REST, sym, start, end):
    return api.get_bars(symbol=sym,
                        timeframe=TimeFrame(1, TimeFrameUnit.Day),
                        start=start,
                        end=end,
                        adjustment='raw').df


def getSetupBars(api: alpaca.REST, setupTime: int, syms: List[str], endSetupDay=None):
    setupBars = {}

    if endSetupDay is None:
        endSetupDay = datetime.datetime.today() - datetime.timedelta(1)

    startSetupDay = calcSetupStartDate(endSetupDay, setupTime)

    startSetupStr = startSetupDay.strftime(DATE_FMT)
    endSetupStr = endSetupDay.strftime(DATE_FMT)

    actualLen = 0
    for x in syms:
        setupBars[x] = getBars(api, x, startSetupStr, endSetupStr)
        actualLen = len(setupBars[x])


    if actualLen < setupTime:
        raise cmErrors.CMError(f'DEV ERR: Not enough setup days, expected: {setupTime}, actual: {actualLen}')

    return setupBars
