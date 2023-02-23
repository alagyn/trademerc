import time
from typing import List, Union, Dict, Tuple, Optional, Any
from .timeframes.timeframe import TimeFrame
import threading
import asyncio

from alpaca.trading.client import TradingClient
import alpaca.trading.requests as tradeReq
import alpaca.trading.enums as tradeEnum
import alpaca.trading.models as models
import alpaca.data.models as dataModels

from cash_money.objects.bar import Bar
from cash_money.objects.order import Order, OrderStatus, OrderType
from cash_money.objects.stock import Stock, CMPosition, StockStatus
from cash_money.trading.notifiers.notifier import Notifier, NotifyKeys
from cash_money.utils.log_utils import CMLogger
from cash_money.cmErrors import CMError
from cash_money.utils.api_utils import CMAPI
from .broker import Broker

log = CMLogger("Alpaca Brkr")


class AlpacaOrder(Order):
    _CANCEL_SET = {"canceled", "expired", "replaced",
                   "pending_cancel", "pending_replace"}

    def __init__(self, o: models.Order):
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
        x = self._data.qty
        return None if x is None else int(x)

    def filledQty(self) -> int:
        x = self._data.filled_qty
        return 0 if x is None else int(x)

    def filledAvgPrice(self) -> float:
        x = self._data.filled_avg_price
        return 0.0 if x is None else float(x)

    def stopPrice(self) -> Union[float, None]:
        x = self._data.stop_price
        return None if x is None else float(x)

    def limitPrice(self) -> Union[float, None]:
        x = self._data.limit_price
        return None if x is None else float(x)

    def data(self) -> Any:
        return self._data


class AlpacaPosition(CMPosition):
    def __init__(self, data: models.Position):
        self._data = data

    def data(self) -> Any:
        return self._data

    def getstatus(self) -> StockStatus:
        if int(self._data.qty) > 0:
            return StockStatus.InMarket
        else:
            return StockStatus.Pending


class AlpacaBroker(Broker):

    def __init__(self, api: CMAPI, symbols: List[str], notifier: Notifier, timeframe: TimeFrame):
        super().__init__(symbols)

        self._notif = notifier

        self._api = api
        self._timeframe = timeframe

        x = self._api.trade.get_account()
        if not isinstance(x, models.TradeAccount):
            raise CMError("AlpacaBroker.__init__() API in raw mode")
        self._account: models.TradeAccount = x
        self._buyPower: float = 0.0
        if self._account.equity is not None:
            self._prevEquity: float = round(float(self._account.equity), 2)

        self._bars = {}

        # List of trades to send in next update
        self._trades = []
        # Dict of order.id -> order
        self._openOrders = {}

        self._api.data.subscribe_bars(self._barUpdateHandler, *symbols)
        log.logInfo("Starting Websocket")
        self._dataThread = threading.Thread(name="Alpaca Data", target=self._api.data.run)
        self._dataThread.start()
        log.logInfo("Init complete")

    def updateAccount(self):
        x = self._api.trade.get_account()
        if not isinstance(x, models.TradeAccount):
            raise CMError()
        self._account = x

    def preRun(self):
        # TODO check for proper shutdown
        # First cancel any existing orders?
        self._api.trade.cancel_orders()
        # Close all positions?
        # self._api.close_all_positions()

    def postRun(self) -> None:
        log.logInfo('Stopping System, Cancelling all existing orders')
        self._api.trade.cancel_orders()
        # Close all positions?
        # self.api.close_all_positions()
        asyncio.run(self._api.data.stop_ws())
        log.logInfo('Done')

    def preTrade(self) -> bool:
        self.updateAccount()

        log.logInfo(f"Begin Trade Step: {self.tradeDay}")

        # Wait for the next TF cycle
        self._timeframe.wait()

        self._updatePositions()
        self._updateBars()

        return True

    def _notifyThread(self):
        self._timeframe.notifyWait()
        self.updateAccount()

        self._updateTrades()
        self._updatePositions()

        if self._account.equity is None:
            raise CMError("AlpacaBroker._notifyThread() Cannot parse equity")
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

        self._notif.update(self._prevEquity, curEquity,
                           totalPL, self._trades, positions)
        self._prevEquity = curEquity
        self._trades = []

    def postTrade(self) -> None:
        if self._notif is not None:
            threading.Thread(target=self._notifyThread).start()
        self._timeframe.postWait()

    def _clock(self) -> models.Clock:
        """Shorcut to get the API clock"""
        return self._api.get_clock()  # type: ignore

    def buyPwr(self) -> float:
        if self._account.buying_power is not None:
            return round(float(self._account.buying_power), 2)
        else:
            # TODO make this not error? don't want it to die unexpectedly
            raise CMError("AlpacaBroker.buyPwr() Cannot get buy pwr")

    async def _barUpdateHandler(self, data: dataModels.bars.Bar):
        self[data.symbol].updateBar(
            Bar(data.low, data.close, data.high, data.volume)
        )

    def _updateBars(self) -> None:
        """
        snaps = self._api.get_snapshots(self.symbols)

        for s in self.symbols:
            db = snaps[s].daily_bar
        """
        print("Bars:")
        for sym, stock in self._stocks.items():
            print(sym, stock.bar)

    def _updatePositions(self):
        x = self._api.trade.get_all_positions()
        if not isinstance(x, List):
            raise CMError()

        positions: List[models.Position] = x
        openset = set()
        for p in positions:
            openset.add(p.symbol)
            try:
                self[p.symbol].position = AlpacaPosition(p)
            except KeyError:
                pass

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
        self._api.trade.cancel_orders()

    def closeAllPositions(self) -> None:
        self._api.trade.close_all_positions(True)

    def getOrder(self, orderid) -> Order:
        x = self._api.trade.get_order_by_id(str(orderid))
        if not isinstance(x, models.Order):
            raise CMError()
        return AlpacaOrder(x)

    def getAllOrders(self) -> Dict[str, Order]:
        """
        :return: Dict OrderID -> Order
        """
        out = {}
        req = tradeReq.GetOrdersRequest(status=tradeEnum.QueryOrderStatus.ALL,
                                        limit=len(self._openOrders),
                                        after=None,
                                        until=None,
                                        direction=None,
                                        nested=None,
                                        side=None,
                                        symbols=None)
        for x in self._api.trade.get_orders(req):
            if not isinstance(x, models.Order):
                raise CMError()

            ao = AlpacaOrder(x)
            out[ao.orderid()] = ao
        return out

    def getPosition(self, symbol: str) -> Any:
        return self._api.trade.get_open_position(symbol)

    def getOpenPositions(self) -> Dict[str, Any]:
        # TODO
        raise NotImplementedError

    def submitBuy(self, stock: Stock, qty: int,
                  stopLimit: Optional[Tuple[float, float]] = None) -> None:

        if stopLimit is None:
            req = tradeReq.OrderRequest(
                symbol=stock.symbol,
                qty=qty,
                notional=None,
                side=tradeEnum.OrderSide.BUY,
                type=tradeEnum.OrderType.MARKET,
                time_in_force=tradeEnum.TimeInForce.DAY,
                order_class=tradeEnum.OrderClass.SIMPLE,
                extended_hours=False,
                client_order_id=None,
                take_profit=None,
                stop_loss=None
            )
            x = self._api.trade.submit_order(req)
            if not isinstance(x, models.Order):
                raise CMError()
            order = x

            stock.stopOrder = None
        else:
            req = tradeReq.OrderRequest(
                symbol=stock.symbol,
                qty=qty,
                notional=None,
                side=tradeEnum.OrderSide.BUY,
                type=tradeEnum.OrderType.MARKET,
                time_in_force=tradeEnum.TimeInForce.DAY,
                # Class: One-Triggers-Other, activates the stop loss after buy is filled
                order_class=tradeEnum.OrderClass.OTO,
                extended_hours=False,
                client_order_id=None,
                take_profit=None,
                stop_loss=tradeReq.StopLossRequest(
                    stop_price=stopLimit[0], limit_price=stopLimit[1])
            )
            x = self._api.trade.submit_order(req)
            if not isinstance(x, models.Order):
                raise CMError()
            order: models.Order = x
            if order.legs is None:
                raise CMError()

            o = AlpacaOrder(order.legs[0])
            self._openOrders[order.legs[0].id] = o
            stock.stopOrder = o

        stock.order = AlpacaOrder(order)
        self._openOrders[order.id] = order

    def _closePosition(self, stock: Stock):
        if stock.stopOrder is not None:
            self._api.trade.cancel_order_by_id(stock.stopOrder.orderid())
            # Force sleep to prevent errors
            time.sleep(0.1)

        order = self._api.trade.close_position(stock.symbol)
        if not isinstance(order, models.Order):
            raise CMError()

        stock.order = None
        stock.stopOrder = None
        stock.lastCloseOrder = AlpacaOrder(order)
        self._openOrders[order.id] = order

    def closePosition(self, stock: Stock) -> None:
        threading.Thread(target=self._closePosition, args=(stock,)).start()

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
        if stopLimit is not None and stock.stopOrder is not None:
            req = tradeReq.ReplaceOrderRequest(
                qty=None,
                time_in_force=None,
                stop_price=stopLimit[0],
                limit_price=stopLimit[1],
                trail=None,
                client_order_id=None)
            order = self._api.trade.replace_order_by_id(stock.stopOrder.orderid(), req)
            if not isinstance(order, models.Order):
                raise CMError()

            stock.stopOrder = AlpacaOrder(order)
