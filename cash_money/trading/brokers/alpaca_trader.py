from typing import List, Union, Dict, Tuple, Optional, Any
from collections import defaultdict
from .timeframes.timeframe import TimeFrame
import threading
import concurrent.futures.thread  # Keep this import to resolve errors in py3.9 /shrug
import asyncio
import datetime
import pytz
import uuid

import alpaca.trading.requests as tradeReq
import alpaca.trading.enums as tradeEnum
import alpaca.common.enums as commonEnum
import alpaca.trading.models as models
import alpaca.data.models.bars as barModels

from cash_money.trading.objects import Order, OrderStatus, OrderType, Bar, Stock, CMPosition, StockStatus
from cash_money.trading.events import Notification
import logging
from cash_money.cmErrors import CMError
from cash_money.utils.api_utils import CMAPI
from cash_money.trading.trader import Trader
from cash_money.trading.nodeStrategy import NodeStrategy
from cash_money.trading.order_db import OrderDB

log = logging.getLogger("Alpaca Brkr")


def checkFractional(value: str) -> int | float:
    if value.find(".") >= 0:
        return float(value)
    return int(value)


class AlpacaOrder(Order):
    _CANCEL_SET = {"canceled", "expired", "pending_cancel"}

    _REPLACE_SET = {"replaced", "pending_replace"}

    def __init__(self, o: models.Order):
        super().__init__(o.id)

        self._data = o

        if self._data.order_type == tradeEnum.OrderType.STOP:
            self._type = OrderType.STOP
        elif self._data.order_type == tradeEnum.OrderType.MARKET:
            if self._data.side == tradeEnum.OrderSide.BUY:
                self._type = OrderType.BUY
            else:
                self._type = OrderType.SELL

        if self._data.status == 'filled':
            self._status = OrderStatus.FILLED
        elif self._data.status in AlpacaOrder._CANCEL_SET:
            self._status = OrderStatus.CANCELED
        elif self._data.status in AlpacaOrder._REPLACE_SET:
            self._status = OrderStatus.REPLACED
        else:
            self._status = OrderStatus.UNFILLED

    def orderType(self) -> OrderType:
        return self._type

    def symbol(self) -> str:
        return self._data.symbol

    def status(self) -> OrderStatus:
        return self._status

    def qty(self) -> float | int:
        if self._data.qty is None:
            return 0
        if isinstance(self._data.qty, str):
            return checkFractional(self._data.qty)
        else:
            return self._data.qty

    def filledQty(self) -> float | int:
        x = self._data.filled_qty
        return 0 if x is None else float(x)

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

    def timestamp(self) -> datetime.datetime:
        if self._data.filled_at is not None:
            return self._data.filled_at
        elif self._data.canceled_at is not None:
            return self._data.canceled_at
        elif self._data.expired_at is not None:
            return self._data.expired_at
        elif self._data.failed_at is not None:
            return self._data.failed_at
        elif self._data.replaced_at is not None:
            return self._data.replaced_at
        elif self._data.submitted_at is not None:
            return self._data.submitted_at
        elif self._data.updated_at is not None:
            return self._data.updated_at

        raise RuntimeError("No timestamp")


class AlpacaPosition(CMPosition):

    def __init__(self, data: models.Position):
        self._data = data

    def data(self) -> Any:
        return self._data

    def getstatus(self) -> StockStatus:
        if float(self._data.qty) > 0:
            return StockStatus.InMarket
        else:
            return StockStatus.Pending

    def qty(self) -> float | int:
        return checkFractional(self._data.qty)


class AlpacaTrader(Trader):

    def __init__(self, strats: Dict[str, NodeStrategy], api: CMAPI, timeframe: TimeFrame):
        super().__init__(strats)

        self._api = api
        self._timeframe = timeframe

        self._db = OrderDB()

        for symbol in self.symbols:
            # noop if already exists
            self._db.addSymbol(symbol)

        x = self._api.trade.get_account()
        if not isinstance(x, models.TradeAccount):
            raise CMError("AlpacaBroker.__init__() API in raw mode")
        self._account: models.TradeAccount = x
        if self._account.equity is not None:
            self._prevEquity: float = round(float(self._account.equity), 2)

        self._bars = {}

        # List of trades to send in next update
        self._next_notification = Notification(self.curDateTime)

        self._api.data.subscribe_bars(self._barUpdateHandler, *self.symbols)
        log.info("Starting Stock Data Websocket")
        self._dataThread = threading.Thread(name="Alpaca Data", target=self._api.data.run)
        self._dataThread.start()

        self._api.trade_stream.subscribe_trade_updates(self._tradeUpdateHandler)
        log.info("Starting Trade Update Websocket")
        self._tradeThread = threading.Thread(name="Alpaca Trade", target=self._api.trade_stream.run)
        self._tradeThread.start()

        self._curDate = datetime.date.today()

        self._followOrders: dict[uuid.UUID, tradeReq.OrderRequest] = {}

        log.info("Init complete")

    def updateAccount(self):
        x = self._api.trade.get_account()
        if not isinstance(x, models.TradeAccount):
            raise CMError()
        self._account = x

    def preRun(self):
        # TODO check for proper shutdown
        # First cancel any existing orders?
        #self._api.trade.cancel_orders()

        self._updatePositions()

        # Update any open orders we know about
        for symbol, stock in self.stocks.items():
            asset = self._api.trade.get_asset(symbol)
            if not isinstance(asset, models.Asset):
                raise RuntimeError()

            stock.fractional = asset.fractionable

            oldest = self._db.getOldestOpenOrder(symbol)
            if oldest is None:
                # try to get the last order we've seen
                oldest = self._db.getLastFilledOrder(symbol)
                if oldest is None:
                    log.debug("Symbol %s: No known orders, asking Alpaca", symbol)
                    # just get the last X orders
                    getOrdersReq = tradeReq.GetOrdersRequest(
                        status=tradeEnum.QueryOrderStatus.ALL,
                        limit=50,
                        after=None,
                        until=None,
                        direction=commonEnum.Sort.DESC,
                        nested=True,
                        side=None,
                        symbols=[symbol]
                    )
            # check if none again, could have found one above
            if oldest is not None:
                # get all orders since the last open order we know of
                afterDate = oldest.timestamp - datetime.timedelta(days=1)
                log.debug("Symbol %s: Getting orders since, %s", symbol, afterDate)
                getOrdersReq = tradeReq.GetOrdersRequest(
                    status=tradeEnum.QueryOrderStatus.ALL,
                    limit=None,
                    after=afterDate,
                    until=None,
                    direction=commonEnum.Sort.DESC,
                    nested=True,
                    side=None,
                    symbols=[symbol]
                )

            orders = self._api.trade.get_orders(getOrdersReq)

            log.debug("Found %d orders", len(orders))

            if not isinstance(orders, list):
                raise RuntimeError()

            cmOrders = [AlpacaOrder(order) for order in orders]

            for order in cmOrders:
                self._db.addOrder(order)

            # TODO stop orders?

            if stock.position is not None:
                if len(orders) == 0:
                    # TODO how to handle a position but no orders?
                    # maybe this won't happen?
                    raise RuntimeError("Open position, but no orders")
                lastOrder = cmOrders[0]
                if lastOrder.orderType() == OrderType.BUY:
                    if lastOrder.qty() != stock.position.qty():
                        # TODO how to handle last buy not having the full qty?
                        # does this matter?
                        log.warning(f'Last order qty != position qty\n{lastOrder.data()}')
                    stock.buyOrder = lastOrder
                    stock.buyDate = stock.buyOrder.timestamp()
                else:
                    # TODO how to handle last order not being a BUY?
                    raise RuntimeError()

    def postRun(self) -> None:
        log.info('Stopping System, Cancelling all existing orders')

        #self._api.trade.cancel_orders()

        # New
        open_orders = self.getAllOrders()
        for order in open_orders.values():
            if order.orderType() != OrderType.STOP:
                self._api.trade.cancel_order_by_id(order.data().id)

        # Close all positions?
        # self.api.close_all_positions()
        asyncio.run(self._api.data.stop_ws())
        asyncio.run(self._api.trade_stream.stop_ws())

        log.info('Done')

    def preTrade(self) -> bool:
        self.updateAccount()

        curDate = datetime.date.today()

        log.info(f"Begin Trade Step: {self.tradeStep}, {self._curDate}")

        self._updatePositions()

        # if daily, tf.postwait will bring us to the start of the next day
        # do this before tf.wait
        if (curDate - self._curDate).days > 0:
            log.info("New day, resubmitting stop orders")
            self._submitNewStopOrders()

        self._curDate = curDate

        # Wait for the next TF cycle
        self._timeframe.wait()

        self._updatePositions()

        return True

    def _notifyThread(self):
        self._timeframe.notifyWait()
        self.updateAccount()

        self._updatePositions()

        if self._account.equity is None:
            raise CMError("AlpacaBroker._notifyThread() Cannot parse equity")
        curEquity = round(float(self._account.equity), 2)

        log.info('Sending Update')
        totalPL = curEquity - self._prevEquity

        # TODO cash
        self._next_notification.equity_prev = self._prevEquity
        self._next_notification.equity_cur = curEquity
        self._next_notification.equity_pl = totalPL

        for sym, s in self.stocks.items():
            if s.position is not None:
                data: models.Position = s.position.data()

                if data.unrealized_pl is None:
                    data.unrealized_pl = "0.0"
                if data.current_price is None:
                    data.current_price = "0.0"
                if data.market_value is None:
                    data.market_value = "0.0"

                self._next_notification.addPosition(
                    symbol=s.symbol,
                    qty=float(data.qty),
                    pl=float(data.unrealized_pl),
                    price=float(data.current_price),
                    value=float(data.market_value),
                    purchaseValue=float(data.avg_entry_price),
                    stopPrice=-1 if s.stopOrder is None else float(s.stopOrder.data().stop_price),
                    lastStop=str(s.lastStopUpdate),
                    nextStop=str(s.nextStopUpdate),
                    purchaseDate="" if s.buyOrder is None else s.buyOrder.data().filled_at
                )
            else:
                self._next_notification.addPosition(s.symbol)

        self.notifyEndOfTradeStep(self._next_notification)
        # TODO This is probably the wrong date
        self._next_notification = Notification(self.curDateTime)
        self._prevEquity = curEquity

    def postTrade(self) -> None:
        threading.Thread(target=self._notifyThread, daemon=True).start()
        self._timeframe.postWait()

    def _clock(self) -> models.Clock:
        """Shortcut to get the API clock"""
        x = self._api.trade.get_clock()
        if not isinstance(x, models.Clock):
            raise RuntimeError()
        return x

    def cash(self) -> float:
        if self._account.cash is not None:
            return round(float(self._account.cash), 2)
        else:
            # TODO make this not error? don't want it to die unexpectedly
            raise CMError("AlpacaBroker.buyPwr() Cannot get cash amount")

    async def _barUpdateHandler(self, data: barModels.Bar | dict):
        if isinstance(data, dict):
            raise RuntimeError("why....")
        # this will only ever give is symbols we care about
        newBar = Bar(data.low, data.close, data.high, data.volume, data.timestamp)
        self.stocks[data.symbol].updateBar(newBar)
        self.notifyStockUpdate(data.symbol, newBar)

    async def _tradeUpdateHandler(self, data: models.TradeUpdate):
        if data.order.symbol not in self.stocks:
            # ignore trades for stocks we don't care about
            return
        # Wrap in our object
        order = AlpacaOrder(data.order)

        log.debug(
            "Trade Update: Sym: %s, type: %s, id: %s, status: %s",
            order.symbol(),
            order.orderType().name,
            order.orderid(),
            order.data().status
        )

        # will update if order exists
        self._db.addOrder(order)

        stock = self.stocks[order.symbol()]
        orderType = order.orderType()

        # TODO make these not error?
        if orderType == OrderType.BUY and stock.buyOrder is None:
            raise RuntimeError("Unknown BUY trade update, Stock.buyOrder is None")
        elif orderType == OrderType.SELL and stock.sellOrder is None:
            raise RuntimeError("Unkown SELL trade update, Stock.sellOrder is None")
        elif orderType == OrderType.STOP and stock.stopOrder is None:
            raise RuntimeError("Unkown STOP trade update, Stock.stopOrder is None")

        self.notifyOrderEvent(order)

        if order.status() != OrderStatus.FILLED:
            return

        qty = order.filledQty()
        price = order.filledAvgPrice()
        value = qty * price

        self._next_notification.addTrade(stock.symbol, order.sideStr(), qty, price, value)

        if orderType == OrderType.BUY:
            log.warning(f"Setting buy date {order.status().name} {order.symbol()} {order.sideStr()}")
            stock.buyDate = self._curDate
        else:
            log.warning(f"Resetting buy date {order.status().name} {order.symbol()} {order.sideStr()}")
            stock.buyDate = None

        if orderType == OrderType.BUY:
            stock.buyOrder = order
        elif orderType == OrderType.STOP:
            stock.stopOrder = order
        elif orderType == OrderType.SELL:
            stock.sellOrder = order

        try:
            x = self._followOrders.pop(order.orderid())
            newOrder = self._api.trade.submit_order(x)
            if not isinstance(newOrder, models.Order):
                raise RuntimeError()
            if isinstance(x, tradeReq.StopOrderRequest):
                stock.stopOrder = AlpacaOrder(newOrder)
        except KeyError:
            pass

    def _updatePositions(self):
        x = self._api.trade.get_all_positions()
        if not isinstance(x, List):
            raise CMError()

        positions: List[models.Position] = x
        openset = set()
        for p in positions:
            openset.add(p.symbol)
            try:
                self.stocks[p.symbol].position = AlpacaPosition(p, )
            except KeyError:
                log.warning(f"Found position for an un-managed symbol: \"{p.symbol}\", ignoring")
                continue
            self.notifyPositionUpdate(p)

        closed = set(self.stocks.keys()).difference(openset)
        for s in closed:
            self.stocks[s].position = None

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
        req = tradeReq.GetOrdersRequest(
            status=tradeEnum.QueryOrderStatus.OPEN,
            limit=None,
            after=None,
            until=None,
            direction=None,
            nested=None,
            side=None,
            symbols=None
        )
        for x in self._api.trade.get_orders(req):
            if not isinstance(x, models.Order):
                raise CMError()

            ao = AlpacaOrder(x)
            out[ao.orderid()] = ao
        return out

    def getPosition(self, symbol: str) -> models.Position:
        x = self._api.trade.get_open_position(symbol)
        if not isinstance(x, models.Position):
            raise RuntimeError()
        return x

    def getOpenPositions(self) -> Dict[str, Any]:
        # TODO
        raise NotImplementedError

    def submitBuy(self, stock: Stock, qty: float | int, stopLoss: Optional[float] = None) -> None:

        if stock.bar is None:
            raise RuntimeError()

        orderID = uuid.uuid4()

        if stopLoss is None:
            req = tradeReq.OrderRequest(
                symbol=stock.symbol,
                qty=qty,
                notional=None,
                side=tradeEnum.OrderSide.BUY,
                type=tradeEnum.OrderType.MARKET,
                time_in_force=tradeEnum.TimeInForce.DAY,
                order_class=tradeEnum.OrderClass.SIMPLE,
                extended_hours=False,
                client_order_id=orderID.hex,
                take_profit=None,
                stop_loss=None
            )
            x = self._api.trade.submit_order(req)
            if not isinstance(x, models.Order):
                raise CMError()
            order = x

            stock.stopOrder = None
        else:

            stopPrice = min(stock.bar.close - 0.02, stopLoss)
            stopPrice = round(stopPrice, 2)
            req = tradeReq.OrderRequest(
                symbol=stock.symbol,
                qty=qty,
                notional=None,
                side=tradeEnum.OrderSide.BUY,
                type=tradeEnum.OrderType.MARKET,
                time_in_force=tradeEnum.TimeInForce.DAY,
                # Class: One-Triggers-Other, activates the stop loss after buy is filled
                order_class=tradeEnum.OrderClass.SIMPLE,
                extended_hours=False,
                client_order_id=orderID.hex
            )

            stopID = uuid.uuid4()
            self._followOrders[orderID] = tradeReq.StopOrderRequest(
                symbol=stock.symbol,
                qty=qty,
                side=tradeEnum.OrderSide.SELL,
                type=tradeEnum.OrderType.MARKET,
                time_in_force=tradeEnum.TimeInForce.DAY,
                stop_price=stopPrice,
                client_order_id=stopID.hex
            )

            x = self._api.trade.submit_order(req)
            if not isinstance(x, models.Order):
                raise CMError()
            order: models.Order = x

        stock.buyOrder = AlpacaOrder(order)

        self._db.addOrder(stock.buyOrder)

    def closePosition(self, stock: Stock):
        if stock.stopOrder is not None:
            self._api.trade.cancel_order_by_id(stock.stopOrder.orderid())

        order = self._api.trade.close_position(stock.symbol)
        if not isinstance(order, models.Order):
            raise CMError()

        stock.sellOrder = AlpacaOrder(order)
        self._db.addOrder(stock.sellOrder)

    def submitSell(self, symbol: str, qty: float) -> Order:
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

    def submitUpdateStop(self, stock: Stock, stopPrice: float) -> None:
        if stock.stopOrder is not None:
            oldStop = stock.stopOrder.stopPrice()
            if oldStop is None:
                raise RuntimeError()

            roundedStop = round(stopPrice, 2)
            if round(oldStop, 2) == roundedStop:
                log.debug("Stop value is the same, not updating")
                return

            oldID = stock.stopOrder.orderid()
            req = tradeReq.ReplaceOrderRequest(
                qty=None,
                time_in_force=None,
                stop_price=roundedStop,
                limit_price=None,
                trail=None,
                client_order_id=None
            )
            order = self._api.trade.replace_order_by_id(stock.stopOrder.orderid(), req)
            if not isinstance(order, models.Order):
                raise CMError()

            log.debug("Submitting update stop, oldID: %s newID: %s", oldID, order.id)
            stock.stopOrder = AlpacaOrder(order)

            self._db.setStop(stock.symbol, stopPrice)

    def now(self) -> datetime.date:
        clock = self._clock()
        return clock.timestamp.astimezone(pytz.timezone("US/Eastern")).date()

    def _submitNewStopOrders(self):
        for stock in self.stocks.values():
            if stock.stopOrder is not None:
                req = tradeReq.StopOrderRequest(
                    symbol=stock.symbol,
                    side=tradeEnum.OrderSide.SELL,
                    type=tradeEnum.OrderType.STOP,
                    time_if_force=tradeEnum.TimeInForce.DAY,
                    stop_price=stock.stopOrder.stopPrice()
                )

                order = self._api.trade.submit_order(req)
                if not isinstance(order, models.Order):
                    raise RuntimeError()
                stock.stopOrder = AlpacaOrder(order)
                self._db.addOrder(stock.stopOrder)
