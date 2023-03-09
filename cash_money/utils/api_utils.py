from configparser import ConfigParser
from typing import Optional, Mapping

from alpaca.trading.client import TradingClient
from alpaca.data.live.stock import StockDataStream
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from cash_money.objects import Bar
import logging

log = logging.getLogger("Alpaca API")


class CMAPI:

    def __init__(self, trade: TradingClient, data: StockDataStream) -> None:
        self.trade = trade
        self.data = data


def loadPaperAPI(apiCfg=None) -> CMAPI:
    if apiCfg is None:
        apiCfg = ConfigParser()
        apiCfg.read('config/system.cfg')
        apiCfg = apiCfg['Alpaca']

    log.info('Initializing Paper Account')
    api_key = str(apiCfg['Paper_API_Key'])
    api_secret = str(apiCfg['Paper_API_Secret'])

    trade = TradingClient(api_key, api_secret, paper=True)
    data = StockDataStream(api_key, api_secret)
    return CMAPI(trade, data)


def loadLiveAPI(apiCfg: Mapping[str, str]) -> CMAPI:
    log.info('Initializing Live Account')
    api_key = str(apiCfg['Live_API_Key'])
    api_secret = str(apiCfg['Live_API_Secret'])

    trade = TradingClient(api_key, api_secret, paper=False)
    data = StockDataStream(api_key, api_secret)

    return CMAPI(trade, data)


def loadAPI(apiCfg, liveRun: bool = False) -> Optional[CMAPI]:
    if liveRun:
        x = input(
            'Are you sure you want to run using the LIVE ACCOUNT? (YES/NO):'
        )
        if x != 'YES':
            return None
        else:
            return loadLiveAPI(apiCfg)

    return loadPaperAPI()


"""
def getBars(api: TradingClient, sym, start, end) -> List[Bar]:
    b = api.get_bars(symbol=sym,
                     timeframe=TimeFrame(1, TimeFrameUnit.Day),
                     start=start,
                     end=end,
                     adjustment='raw').df
    return [Bar(b['low'][i], b['close'][i], b['high'][i], b['volume']) for i in range(len(b))]
"""
