from datetime import datetime
from cash_money.trading.data.dataBroker import BarDict
from cash_money.trading.objects import Bar
from .dataBroker import DataBroker

from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.models.bars import BarSet
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


class AlpacaDataBroker(DataBroker):

    def __init__(self, apiCfg) -> None:
        super().__init__()

        try:
            key = apiCfg["Paper_API_Key"]
            secret = apiCfg["Paper_API_Secret"]
        except KeyError:
            key = apiCfg["Live_API_Key"]
            secret = apiCfg["Live_API_Secret"]

        self._client = StockHistoricalDataClient(key, secret)

    def getBars(self, symbols: list[str], startDate: datetime, endDate: datetime) -> BarDict:
        req = StockBarsRequest(
            symbol_or_symbols=symbols,
            start=startDate,
            end=endDate,
            timeframe=TimeFrame(1, TimeFrameUnit.Day),
        )

        data = self._client.get_stock_bars(req)

        if not isinstance(data, BarSet):
            raise RuntimeError()

        out: BarDict = {
            sym: list()
            for sym in symbols
        }

        for symbol in symbols:
            barList = out[symbol]
            rawBars = data.data[symbol]

            for rawBar in rawBars:
                barList.append(Bar(rawBar.low, rawBar.close, rawBar.high, rawBar.volume, rawBar.timestamp))

        return out
