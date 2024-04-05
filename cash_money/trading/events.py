from typing import List
from cash_money.trading.objects import Action, Bar, Order, CMPosition
from datetime import datetime


class TradeNotification:

    def __init__(self, symbol: str, side: str, qty: int, price: float, value: float) -> None:
        self.symbol = symbol
        self.side = side
        self.qty = qty
        self.price = price
        self.value = value


class PositionNotification:

    def __init__(
        self,
        symbol: str,
        qty: int,
        pl: float,
        price: float,
        value: float,
        purchaseValue: float,
        stopPrice: float,
        lastStop: str,
        nextStop: str,
        purchaseDate: str
    ) -> None:
        self.symbol = symbol
        # Total quantity
        self.qty = qty
        # Profit/Loss
        self.pl = pl
        # Current prive
        self.price = price
        # Total value
        self.value = value
        # Avg price per stock when bought
        self.purchashValue = purchaseValue
        # Stop-loss price
        self.stopPrice = stopPrice
        # date of last stop update
        self.lastStop = lastStop
        # date of next stop update
        self.nextStop = nextStop
        # Date of purchase
        self.purchaseDate = purchaseDate


class Notification:

    def __init__(self, date: datetime) -> None:
        self.cash = 0.0
        self.equity_prev = 0.0
        self.equity_cur = 0.0
        self.equity_pl = 0.0

        self.trades: List[TradeNotification] = []
        self.positions: List[PositionNotification] = []
        self.date = date

    def addPosition(
        self,
        symbol: str,
        qty: int = 0,
        pl: float = 0,
        price: float = 0,
        value: float = 0,
        purchaseValue: float = 0,
        stopPrice: float = 0,
        lastStop: str = "",
        nextStop: str = "",
        purchaseDate: str = ""
    ):
        self.positions.append(
            PositionNotification(
                symbol=symbol,
                qty=qty,
                pl=pl,
                price=price,
                value=value,
                purchaseValue=purchaseValue,
                stopPrice=stopPrice,
                lastStop=lastStop,
                nextStop=nextStop,
                purchaseDate=purchaseDate
            )
        )

    def addTrade(self, symbol: str, side: str, qty: int, price: float, value: float) -> None:
        self.trades.append(TradeNotification(symbol=symbol, side=side, qty=qty, price=price, value=value))


class ActionEvent:

    def __init__(self, action: Action) -> None:
        self.action = action


class OrderEvent:

    def __init__(self, order: Order) -> None:
        self.order = order


class EndOfTradeStepEvent:

    def __init__(self, n: Notification) -> None:
        self.notif = n


class PositionUpdateEvent:

    def __init__(self, position: CMPosition) -> None:
        self.position = position


class StockUpdateEvent:

    def __init__(self, symbol: str, bar: Bar) -> None:
        self.bar = bar
        self.symbol = symbol


class ErrorEvent:

    def __init__(self, message: str) -> None:
        self.message = message


class CMEventListener:
    """
    CashMoney Event Listener interface
    """

    def onAction(self, event: ActionEvent):
        pass

    def onOrder(self, event: OrderEvent):
        pass

    def onPositionUpdate(self, event: PositionUpdateEvent):
        pass

    def onStockUpdate(self, event: StockUpdateEvent):
        pass

    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        pass

    def onError(self, event: ErrorEvent):
        pass
