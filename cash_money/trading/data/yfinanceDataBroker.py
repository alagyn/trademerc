from datetime import datetime
from cash_money.trading.objects import Bar
from cash_money.utils.date_utils import nextBusinessDay
from .dataBroker import DataBroker, BarDict

import yfinance as yf
import pandas as pd


def parseYFDate(d) -> datetime:
    return d.to_pydatetime()


class YFinanceDataBroker(DataBroker):

    def __init__(self, dataDBDir: str) -> None:
        super().__init__(dataDBDir)

    def _getBars(self, symbols: list[str], startDate: datetime, endDate: datetime) -> BarDict:
        dirtyBars: dict[str, list[Bar]] = {}
        dl = yf.download(symbols, startDate, endDate, progress=False, auto_adjust=False)
        if dl is None:
            raise RuntimeError("Failed to download data")
        b: pd.DataFrame = dl
        for sym in symbols:
            bars = []
            for index, row in b.iterrows():
                bars.append(
                    Bar(row['Low'][sym], row['Close'][sym], row['High'][sym], row["Volume"][sym], parseYFDate(index))
                )
            dirtyBars[sym] = bars

        # Normalize all the bars
        # Make the lists of bars have the same date at every index
        # Bar entries won't have a bar if there was no data for that day
        cleanBarsDict: BarDict = {
            sym: list()
            for sym in symbols
        }
        curDate = min([x[0].date for x in dirtyBars.values()])

        # Dict of current indices for each symbol
        idxs = {
            sym: 0
            for sym in symbols
        }

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
                    cleanBarsDict[sym].append(None)

            # If we don't have any bars for this date (probably a holiday)
            if not haveBar:
                # Then we have a row of empty BarEntries
                for sym in idxs:
                    # Remove them
                    cleanBarsDict[sym].pop()

            # Go to next business day
            curDate = nextBusinessDay(curDate)

        return cleanBarsDict
