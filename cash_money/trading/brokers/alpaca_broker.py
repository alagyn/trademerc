import time
from typing import List, Union, Dict, Tuple, Optional
from .timeframes.timeframe import TimeFrame
import threading

import alpaca_trade_api as alpaca

from cash_money.objects.bar import Bar
from cash_money.objects.order import Order, OrderStatus, OrderType
from cash_money.objects.stock import Stock, CMPosition, StockStatus
from cash_money.trading.notifiers.notfier import Notifier, NotifyKeys
from cash_money.utils.log_utils import CMLogger
from .broker import Broker

log = CMLogger("Alpaca Brkr")

class AlpacaOrder(Order):
    _CANCEL_SET = {"canceled", "expired", "replaced", "pending_cancel", "pending_replace"}

    def __init__(self, o: alpaca.rest.Order):
        super().__init__(o.id)

        self._data = o
        if self._data.side == 'sell':
            self._type = OrderType.SELL
        elif self._data.legs is not None and len(self._data.legs) > 0:
            self._type = OrderType.BUY_AND_STOP
        else:
            self._type = OrderType.BUY

        if self._data.status == 'filled':
            self._status = OrderStatus.FILLED
        elif self._data.status in AlpacaOrder._CANCEL_SET:
            self._status = OrderStatus.CANCELED
        else:
            self._status = OrderStatus.UNFILLED

    def orderType(self) -> OrderType:
        return self._type

    def symbol(self) -> str:
        return self._data.symbol

    def status(self) -> OrderStatus:
        return self._status

    def qty(self) -> Union[int, None]:
        return self._data.qty

    def filledQty(self) -> int:
        return int(self._data.filled_qty)

    def filledAvgPrice(self) -> float:
        return float(self._data.filled_avg_price)

    def stopPrice(self) -> Union[float, None]:
        return self._data.stop_price

    def limitPrice(self) -> Union[float, None]:
        return self._data.limit_price

    def data(self) -> any:
        return self._data

class AlpacaPosition(CMPosition):
    def __init__(self, data: alpaca.rest.Position):
        self._data = data

    def data(self) -> any:
        return self._data

    def getstatus(self) -> StockStatus:
        if int(self._data.qty) > 0:
            return StockStatus.InMarket
        else:
            return StockStatus.Pending

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
        log.logInfo('Stopping System, Cancelling all existing orders')
        self._api.cancel_all_orders()
        # Close all positions?
        # self.api.close_all_positions()
        log.logInfo('Done')

    def preTrade(self) -> bool:
        self._account = self._api.get_account()

        log.logInfo(f"Begin Trade Step: {self.tradeDay}")

        # Wait for the next TF cycle
        self._timeframe.wait()

        self._updatePositions()
        self._updateBars()

        return True

    def _notifyThread(self):
        time.sleep(self._timeframe.notifyWait())
        self._account = self._api.get_account()

        self._updateTrades()
        self._updatePositions()

        curEquity = round(float(self._account.equity), 2)

        log.logInfo('Sending Update')
        totalPL = curEquity - self._prevEquity

        positions = []
        for sym, s in self._stocks.items():
            if s.position is not None:
                data = s.position.data()
                p = {
                    NotifyKeys.Position.Symbol: s.symbol,
                    NotifyKeys.Position.Qty: data.qty,
                    NotifyKeys.Position.PL: data.unrealized_pl,
                    NotifyKeys.Position.Price: data.current_price,
                    NotifyKeys.Position.Value: data.market_value,
                    NotifyKeys.Position.PurchaseValue: data.avg_entry_price,
                    NotifyKeys.Position.LastStop: s.lastStopUpdate,
                    NotifyKeys.Position.NextStop: s.nextStopUpdate
                }

                if s.order is not None:
                    p[NotifyKeys.Position.PurchaseDate] = s.order.data().filled_at
                if s.stopOrder is not None:
                    p[NotifyKeys.Position.StopPrice] = s.stopOrder.data().stop_price

            else:
                p = {
                    NotifyKeys.Position.Symbol: s.symbol,
                    NotifyKeys.Position.Qty: 0
                }
            positions.append(p)

        self._notif.update(self._prevEquity, curEquity, totalPL, self._trades, positions)
        self._prevEquity = curEquity
        self._trades = []

    def postTrade(self) -> None:
        if self._notif is not None:
            threading.Thread(target=self._notifyThread).start()
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
        positions: List[alpaca.rest.Position] = self._api.list_positions()
        openset = set()
        for p in positions:
            openset.add(p.symbol)
            self[p.symbol].position = AlpacaPosition(p)

        closed = self._stocks.keys() - openset
        for s in closed:
            self[s].position = None

    def _updateTrades(self):
        filled = []
        orders = self.getAllOrders()
        for orderid in self._openOrders:
            try:
                order = orders[orderid]
            except KeyError:
                order = self.getOrder(orderid)

            if order.status() == OrderStatus.FILLED:
                filled.append(orderid)

                qty = int(order.filledQty())
                price = float(order.filledAvgPrice())
                value = qty * price

                t = {
                    NotifyKeys.Trade.Symbol: order.symbol(),
                    NotifyKeys.Trade.Side: order.side(),
                    NotifyKeys.Trade.Qty: qty,
                    NotifyKeys.Trade.Price: price,
                    NotifyKeys.Trade.Value: value
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

    def getAllOrders(self) -> Dict[str, Order]:
        """
        :return: Dict OrderID -> Order
        """
        out = {}
        for x in self._api.list_orders(status="all", limit=len(self._openOrders)):
            ao = AlpacaOrder(x)
            out[ao.orderid()] = ao
        return out

    def getPosition(self, symbol: str) -> any:
        return self._api.get_position(symbol)

    def getOpenPositions(self) -> Dict[str, any]:
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
            stock.stopOrder = o

        stock.order = AlpacaOrder(order)
        self._openOrders[order.id] = order

    def closePosition(self, stock: Stock) -> None:
        if stock.stopOrder is not None:
            self._api.cancel_order(stock.stopOrder.orderid())
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
        raise NotImplementedError

    def submitUpdateStop(self, stock: Stock, stopLimit: Optional[Tuple[float, float]]) -> None:
        order = self._api.replace_order(order_id=stock.stopOrder.orderid(),
                                        stop_price=f"{stopLimit[0]:.2f}",
                                        limit_price=f"{stopLimit[1]:.2f}")

        stock.stopOrder = AlpacaOrder(order)
