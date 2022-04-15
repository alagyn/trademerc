
from configparser import ConfigParser
from typing import List

import alpaca_trade_api as alpaca
from alpaca_trade_api import TimeFrame, TimeFrameUnit
from alpaca_trade_api.common import URL

from consts import LIVE_ENDPOINT, PAPER_ENDPOINT
from objects.bar import Bar
from utils.log_utils import logInfo as _logInfo

def logInfo(m):
    _logInfo("Alpaca API", m)


def loadPaperAPI(apiCfg=None):
    if apiCfg is None:
        apiCfg = ConfigParser()
        apiCfg.read('config/system.cfg')
        apiCfg = apiCfg['Alpaca']

    logInfo('Initializing Paper Account')
    api_key = str(apiCfg['Paper_API_Key'])
    api_secret = str(apiCfg['Paper_API_Secret'])
    endpoint = PAPER_ENDPOINT
    return alpaca.REST(api_key, api_secret, URL(endpoint), 'v2')


def loadLiveAPI(apiCfg=None):
    logInfo('Initializing Live Account')
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


def getBars(api: alpaca.REST, sym, start, end) -> List[Bar]:
    b = api.get_bars(symbol=sym,
                        timeframe=TimeFrame(1, TimeFrameUnit.Day),
                        start=start,
                        end=end,
                        adjustment='raw').df
    return [Bar(b['low'][i], b['close'][i], b['high'][i]) for i in range(len(b))]

