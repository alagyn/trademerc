from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
import os

from cash_money.trading.objects import Bar

BarList = List[Optional[Bar]]
BarDict = Dict[str, BarList]

# yapf: disable
SYMBOL_LIST_SCHEMA = """
CREATE TABLE IF NOT EXISTS 
    symbols
(
 symbol TEXT NOT NULL
)
"""

ADD_SYMBOL = """
INSERT INTO
    symbols (symbol)
VALUES
    (?)
"""

GET_SYMBOL = """
SELECT * FROM symbols WHERE symbol = ?
"""

RANGE_SCHEMA = """
CREATE TABLE IF NOT EXISTS
    ranges_{0}
(
    start_ts INTEGER NOT NULL,
    end_ts INTEGER NOT NULL
)
"""

ADD_RANGE = """
INSERT INTO
    ranges_{0}
    (start_ts, end_ts)
VALUES
    (:start_ts, :end_ts)
"""

GET_RANGES = """
SELECT
    start_ts, end_ts
FROM
    ranges_{0}
WHERE
    (start_ts <= :want_start AND :want_start <= end_ts)
    OR
    (start_ts <= :want_end AND :want_end <= end_ts)
    OR
    (:want_start <= start_ts AND end_ts <= :want_end)
"""

DATA_SCHEMA = """
CREATE TABLE IF NOT EXISTS
    data_{0}
(
    ts INTEGER UNIQUE NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    high REAL NOT NULL,
    volume REAL NOT NULL
)
"""

DATA_INDEX = """
CREATE INDEX IF NOT EXISTS
    data_{0}_ts ON data_{0}
(
    ts
)
"""

GET_DATA = """
SELECT
    ts, low, close, high, volume
FROM
    data_{0}
WHERE
    :want_start <= ts AND ts <= :want_end
"""

ADD_DATA = """
INSERT INTO
    data_{0}
    (ts, low, close, high, volume)
VALUES
    (:ts, :low, :close, :high, :volume)
ON CONFLICT DO NOTHING
"""

# yapf: enable


class DataBroker:

    def __init__(self, dataDBPath: str) -> None:
        needInit = not os.path.exists(dataDBPath)

        self._con = sqlite3.connect(dataDBPath, check_same_thread=False)

        if needInit:
            cur = self._con.cursor()
            cur.execute(SYMBOL_LIST_SCHEMA)
            self._con.commit()

    def getBars(self, symbols: list[str], startDate: datetime, endDate: datetime) -> BarDict:
        startTS = startDate.timestamp()
        endTS = endDate.timestamp()

        out: BarDict = {}

        cur = self._con.cursor()
        for symbol in symbols:
            res = cur.execute(GET_SYMBOL, symbol)
            data = res.fetchone()

            if data is None:
                cur.execute(RANGE_SCHEMA.format(symbol))
                cur.execute(DATA_SCHEMA.format(symbol))
                cur.execute(DATA_INDEX.format(symbol))
                # TODO short circuit, just download everything
            else:
                timeArgs = {
                    'want_start': startTS,
                    'want_end': endTS
                }
                res = cur.execute(GET_RANGES.format(symbol), timeArgs)
                existingRanges = res.fetchall()
                isCached = False
                for a, b in existingRanges:
                    if a <= startTS and endTS <= b:
                        # we have it cached
                        isCached = True
                        break

                if isCached:
                    res = cur.execute(GET_DATA.format(symbol), timeArgs)
                    barData = []
                    for ts, low, close, high, volume in res:
                        barData.append(Bar(low, close, high, volume, datetime.fromtimestamp(ts)))
                else:
                    barData = self._getBars(symbol, startDate, endDate)
                    for bar in barData:
                        if bar is not None:
                            cur.execute(
                                ADD_DATA,
                                {
                                    "ts": bar.date.timestamp(),
                                    "low": bar.lo,
                                    "close": bar.close,
                                    "high": bar.hi,
                                    "volume": bar.vol
                                }
                            )

                out[symbol] = barData

        self._con.commit()

        return out

    def _getBars(self, symbol: str, startDate: datetime, endDate: datetime) -> BarList:
        raise NotImplementedError()
