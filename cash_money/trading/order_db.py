import sqlite3
import uuid
import os
import datetime
import logging
import threading

from cash_money.trading.objects import Order, OrderType, OrderStatus
from cash_money.utils.run_utils import CONFIG_DIR

# yapf: disable
SYMBOL_LIST_SCHEMA = """
CREATE TABLE IF NOT EXISTS 
    symbols
(
 symbol TEXT NOT NULL,
 stop_price REAL
)
"""

ADD_SYMBOL = """
INSERT INTO
    symbols (symbol, stop_price)
VALUES
    (?, NULL)
"""

CHECK_SYMBOL = """
SELECT
    count(*)
FROM
    symbols
WHERE
    symbol = ?
"""

GET_STOP = """
SELECT 
    stop_price
FROM
    symbols
WHERE
    symbol = ?
"""

SET_STOP = """
UPDATE
    symbols
SET
    stop_price = :stop_price
WHERE
    symbol = :symbol
"""

ORDER_SCHEMA = """
CREATE TABLE IF NOT EXISTS
    orders_{0}
(
    order_id BLOB UNIQUE NOT NULL,
    timestamp INTEGER NOT NULL,
    side INTEGER NOT NULL,
    qty INTEGER NOT NULL,
    status INTEGER NOT NULL
)
"""

ORDER_INDEX = """
CREATE INDEX IF NOT EXISTS
    orders_{0}_ts ON orders_{0}
(
    timestamp
)
"""

ADD_ORDER = """
INSERT INTO
    orders_{}
    (order_id, timestamp, side, qty, status)
VALUES
    (:order_id, :timestamp, :side, :qty, :status)
ON CONFLICT DO UPDATE SET
    timestamp = excluded.timestamp,
    qty = excluded.qty,
    status = excluded.status
"""

UPDATE_ORDER = """
UPDATE
    orders_{0}
SET
    status = :status
WHERE
    order_id = :order_id
"""

GET_OPEN_ORDERS = """
SELECT 
    order_id, timestamp
FROM
    orders_{0}
WHERE
    status = 0 AND side <= 1 
"""

GET_OLDEST_OPEN_ORDER = """
SELECT
    order_id, timestamp, side, qty, status
FROM 
    orders_{0}
WHERE
    status = 0
ORDER BY
    timestamp ASC
LIMIT 1
"""

GET_LAST_ORDER = """
SELECT
    order_id, timestamp, side, qty, status
FROM
    orders_{0}
ORDER BY
    timestamp DESC
LIMIT 1
"""
# yapf: enable

ORDER_DB_FILE = os.path.join(CONFIG_DIR, "orders.db")

log = logging.getLogger("OrderDB")


def threadlock(func):

    def wrapper(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)

    return wrapper


class DBOrder:

    def __init__(
        self, oID: uuid.UUID, timestamp: datetime.datetime, side: OrderType, qty: int, status: OrderStatus
    ) -> None:
        self.order_id = oID
        self.timestamp = timestamp
        self.side = side
        self.qty = qty
        self.status = status


class OrderDB:

    def __init__(self) -> None:
        needInit = not os.path.exists(ORDER_DB_FILE)
        self.lock = threading.Semaphore()
        self._con = sqlite3.connect(ORDER_DB_FILE, check_same_thread=False)

        if needInit:
            cur = self._con.cursor()
            cur.execute(SYMBOL_LIST_SCHEMA)
            self._con.commit()

    @threadlock
    def addSymbol(self, symbol: str):
        log.debug("Adding symbol %s", symbol)
        cur = self._con.cursor()
        res = cur.execute(CHECK_SYMBOL, (symbol, ))
        data = res.fetchone()
        if data is not None and data[0] > 0:
            log.debug("Symbol already exists: %s", symbol)
            return

        log.debug("Adding symbol: %s", symbol)

        cur.execute(ADD_SYMBOL, (symbol, ))
        cur.execute(ORDER_SCHEMA.format(symbol))
        cur.execute(ORDER_INDEX.format(symbol))

        self._con.commit()

    @threadlock
    def addOrder(self, order: Order):
        cur = self._con.cursor()
        cur.execute(
            ADD_ORDER.format(order.symbol()),
            {
                "order_id": order.orderid().bytes,
                "timestamp": order.timestamp().timestamp(),
                "side": order.orderType().value,
                "qty": order.qty(),
                "status": order.status().value
            }
        )
        self._con.commit()

    @threadlock
    def getStop(self, symbol: str) -> float:
        cur = self._con.cursor()
        res = cur.execute(GET_STOP, (symbol, ))
        out = float(res.fetchone()[0])
        return out

    @threadlock
    def setStop(self, symbol: str, stop: float):
        cur = self._con.cursor()
        cur.execute(SET_STOP, {
            "symbol": symbol,
            "stop_price": stop
        })
        self._con.commit()

    @threadlock
    def updateOrderStatus(self, order: Order):
        cur = self._con.cursor()
        cur.execute(
            UPDATE_ORDER.format(order.symbol()), {
                "status": order.status().value,
                "order_id": order.orderid().bytes
            }
        )
        self._con.commit()

    @threadlock
    def getOldestOpenOrder(self, symbol: str) -> DBOrder | None:
        cur = self._con.cursor()
        res = cur.execute(GET_OLDEST_OPEN_ORDER.format(symbol))
        data = res.fetchone()
        if data is None:
            return None

        return DBOrder(
            uuid.UUID(bytes=data[0]),
            datetime.datetime.fromtimestamp(data[1]),
            OrderType(data[2]),
            data[3],
            OrderStatus(data[4])
        )

    @threadlock
    def getOpenOrders(self, symbol: str) -> list[tuple[uuid.UUID, datetime.datetime]]:
        cur = self._con.cursor()
        res = cur.execute(GET_OPEN_ORDERS.format(symbol))
        return [(uuid.UUID(bytes=x[0]), datetime.datetime.fromtimestamp(x[1])) for x in res.fetchall()]

    @threadlock
    def getLastFilledOrder(self, symbol: str) -> DBOrder | None:
        cur = self._con.cursor()
        res = cur.execute(GET_LAST_ORDER.format(symbol))
        data = res.fetchone()
        if data is None:
            return None

        return DBOrder(
            uuid.UUID(bytes=data[0]),
            datetime.datetime.fromtimestamp(data[1]),
            OrderType(data[2]),
            data[3],
            OrderStatus(data[4])
        )
