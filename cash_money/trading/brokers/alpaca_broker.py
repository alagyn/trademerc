import datetime
import time
from abc import ABC
from time import sleep
from typing import List, Union, Dict, Tuple, Optional

import alpaca_trade_api as alpaca

from cash_money.objects.bar import Bar
from cash_money.objects.order import Order, OrderStatus, OrderType
from cash_money.objects.position import Position
from cash_money.objects.stock import Stock
from cash_money.trading.notifiers.notfier import Notifier
from cash_money.utils.log_utils import logInfo as _logInfo
from .broker import Broker


def logInfo(m):
    _logInfo("Alpaca Brkr", m)


def toTS(t):
    return t.replace(tzinfo=datetime.timezone.utc).timestamp()


MARKET_CLOSE_DELTA = 15 * 60


def logTF(m):
    _logInfo("Timeframe", m)


class TimeFrame(ABC):
    def __init__(self, api: alpaca.REST):
        self._api = api

    def wait(self) -> None:
        raise NotImplementedError

    def postWait(self) -> None:
        raise NotImplementedError

    def _waitForTS(self, ts):
        """Utility to wait until timestamp"""

        while True:
            clock = self._api.get_clock()
            diff = ts - toTS(clock.timestamp)
            if diff <= 0:
                return

            if diff > 6:
                logTF(f'Sleeping {diff / 60:.2f}min')
                timeToSleep = diff - 5
                sleep(timeToSleep)
            else:
                sleep(2)


class SecTF(TimeFrame):
    def __init__(self, api: alpaca.REST, secs: float):
        super().__init__(api)
        self.secs = secs

    def wait(self) -> None:
        clock = self._api.get_clock()
        timeToClose = toTS(clock.next_close)
        timeToOpen = toTS(clock.next_open)
        now = toTS(clock.timestamp)

        if not clock.is_open or now + self.secs + 0.5 > timeToClose:
            logTF(f"Sleeping until market opens")
            self._waitForTS(timeToOpen + 1)
        else:
            logTF(f"Sleeping {self.secs}sec")
            time.sleep(self.secs)

    def postWait(self) -> None:
        # ILB
        pass


class DailyTF(TimeFrame):
    def __init__(self, api: alpaca.REST, anchor: str, minoffset: float):
        super(DailyTF, self).__init__(api)
        if anchor == "open":
            self.anchorStart = True
        elif anchor == "close":
            self.anchorStart = False
        else:
            raise RuntimeError(f"Invalid anchor: {anchor}")

        self._secs = minoffset * 60
        self._min = f"{minoffset:.2f}min"

    def wait(self):
        clock = self._api.get_clock()

        if self.anchorStart:
            logTF(f"Sleeping until {self._min} after Open")
            timeToOpen = toTS(clock.next_open)
            self._waitForTS(timeToOpen + self._secs)
        else:
            logTF(f"Sleeping until {self._min} before close")
            timeToClose = toTS(clock.next_close)
            self._waitForTS(timeToClose - self._secs)

    def postWait(self) -> None:
        clock = self._api.get_clock()

        logTF(f'Forcing sleep until open')
        timeToOpen = toTS(clock.next_open)
        self._waitForTS(timeToOpen)


class AlpacaOrder(Order):
    _CANCEL_SET = {"canceled", "expired", "replaced", "pending_cancel", "pending_replace"}

    def __init__(self, o: alpaca.rest.Order):
        super().__init__(o.orderid)
        self._o = o
        if self._o.side == 'sell':
            self._type = OrderType.SELL
        elif self._o.legs is not None and len(self._o.legs) > 0:
            self._type = OrderType.BUY_AND_STOP
        else:
            self._type = OrderType.BUY

        if self._o.status == 'filled':
            self._status = OrderStatus.FILLED
        elif self._o.status in AlpacaOrder._CANCEL_SET:
            self._status = OrderStatus.CANCELED
        else:
            self._status = OrderStatus.UNFILLED

    def orderType(self) -> OrderType:
        return self._type

    def symbol(self) -> str:
        return self._o.symbol

    def status(self) -> OrderStatus:
        return self._status

    def qty(self) -> Union[int, None]:
        return self._o.qty

    def filledQty(self) -> int:
        return int(self._o.filled_qty)

    def filledAvgPrice(self) -> float:
        return float(self._o.filled_avg_price)

    def stopPrice(self) -> Union[float, None]:
        return self._o.stop_price

    def limitPrice(self) -> Union[float, None]:
        return self._o.limit_price

    def data(self, key: str) -> any:
        return self._o[key]


class AlpacaBroker(Broker):

    def __init__(self, api: alpaca.REST, symbols: List[str], notifier: Notifier, timeframe: TimeFrame):
        super().__init__(symbols)

        self._notif = notifier

        self._api = api
        self._timeframe = timeframe

        self._account = self._api.get_account()
        self._buyPower: float = 0.0
        self._prevEquity = round(float(self._account.equity), 2)

        self._bars = {}

        # List of trades to send in next update
        self._trades = []
        # Dict of order.id -> order
        self._openOrders = {}

    def preRun(self):
        # TODO check for proper shutdown
        # First cancel any existing orders?
        self._api.cancel_all_orders()
        # Close all positions?
        # self._api.close_all_positions()

    def postRun(self) -> None:
        logInfo('Stopping System, Cancelling all existing orders')
        self._api.cancel_all_orders()
        # Close all positions?
        # self.api.close_all_positions()
        logInfo('Done')

    def preTrade(self) -> bool:
        self._account = self._api.get_account()

        logInfo(f"Begin Trade Step: {self.tradeDay}")

        # Wait for the next TF cycle
        self._timeframe.wait()

        self._updateBars()

        return True

    def postTrade(self) -> None:

        self._account = self._api.get_account()

        self._updateTrades()

        curEquity = round(float(self._account.equity), 2)

        if self._notif is not None:
            logInfo('Sending Update')
            totalPL = curEquity - self._prevEquity

            positions = []
            for sym, s in self._stocks.items():
                if s.position is not None:
                    p = {
                        'symbol': s.symbol,
                        'qty': s.position.qty,
                        'pl': s.position.unrealized_pl,
                        'price': s.position.current_price,
                        'value': s.position.market_value,
                        'p_value': s.position.avg_entry_price,
                        'p_date': s.order().data("filled_at"),
                        'stop_price': s.stopOrder().data("stop_price"),
                        'last_stop': s.lastStopUpdate,
                        'next_stop': s.nextStopUpdate
                    }
                    positions.append(p)

            self._notif.update(self._prevEquity, curEquity, totalPL, self._trades, positions)

        self._prevEquity = curEquity
        self._trades = []

        self._timeframe.postWait()

    def _clock(self) -> alpaca.rest.Clock:
        """Shorcut to get the API clock"""
        return self._api.get_clock()

    def buyPwr(self) -> float:
        return round(float(self._account.buying_power), 2)

    def _updateBars(self) -> None:
        snaps = self._api.get_snapshots(self.symbols)

        for s in self.symbols:
            db = snaps[s].daily_bar
            self[s].updateBar(Bar(db.l, db.c, db.h, db.v))

    def _updatePositions(self):
        positions = self._api.list_positions()
        openset = set()
        for p in positions:
            openset.add(p.symbol)

            self[p.symbol].position = p

        closed = self._stocks.keys() - openset
        for s in closed:
            self[s].position = None

    def _updateTrades(self):
        filled = []
        orders = self.getAllOrders()
        for orderid in self._openOrders:
            order = orders[orderid]

            if order.status() == OrderStatus.FILLED:
                filled.append(orderid)

                qty = int(order.filledQty())
                price = float(order.filledAvgPrice())
                value = qty * price

                t = {
                    'symbol': order.symbol,
                    'side': order.side,
                    'qty': qty,
                    'price': price,
                    'value': value
                }

                self._trades.append(t)

        for x in filled:
            del self._openOrders[x]

    def cancelAllOrders(self) -> None:
        self._api.cancel_all_orders()

    def closeAllPositions(self) -> None:
        self._api.close_all_positions()

    def getOrder(self, orderid) -> Order:
        return AlpacaOrder(self._api.get_order(str(orderid)))

    def getAllOrders(self) -> List[Order]:
        return [AlpacaOrder(x) for x in self._api.list_orders()]

    def getPosition(self, symbol: str) -> Position:
        return self._api.get_position(symbol)

    def getOpenPositions(self) -> Dict[str, Position]:
        # TODO
        raise NotImplementedError

    def submitBuy(self, stock: Stock, qty: int,
                  stopLimit: Optional[Tuple[float, float]] = None) -> None:

        if stopLimit is None:
            order = self._api.submit_order(
                symbol=stock.symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='day'
            )

            stock.stopOrder = None
        else:
            order: alpaca.rest.Order = self._api.submit_order(
                symbol=stock.symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='day',

                # Class: One-Triggers-Other, activates the stop loss after buy is filled
                order_class='oto',
                stop_loss={
                    'stop_price': stopLimit[0],
                    'limit_price': stopLimit[1]
                }
            )
            o = AlpacaOrder(order.legs[0])
            self._openOrders[order.legs[0].id] = o
            stock.stopOrder(o)

        stock.order(AlpacaOrder(order))
        self._openOrders[order.id] = order

    def closePosition(self, stock: Stock) -> None:
        order = self._api.close_position(symbol=stock.symbol)
        stock.order = None
        stock.stopOrder = None
        stock.lastCloseOrder = order
        self._openOrders[order.id] = order

    def submitSell(self, symbol: str, qty: int) -> Order:
        """
                try:
                    order = self.api.submit_order(
                        symbol=action.symbol,
                        qty=action.args['qty'],
                        side='sell',
                        type='market',
                        time_in_force='day',
                    )
                except KeyError as err:
                    raise cmErrors.ActionError(f'Action missing argument: "{str(err)}", Action: {str(action)}')
                except alpaca.rest.APIError:
                    # error submitting order
                    pass
        """
        pass

    def submitUpdateStop(self, stock: Stock, stopLimit: Optional[Tuple[float, float]]) -> None:
        order = self._api.replace_order(order_id=stock.stopOrder().orderid(),
                                        stop_price=f"{stopLimit[0]:.2f}",
                                        limit_price=f"{stopLimit[1]:.2f}")

        stock.stopOrder(AlpacaOrder(order))
