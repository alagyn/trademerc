from typing import List


class TradeNotification:
    def __init__(self,
                 symbol: str,
                 side: str,
                 qty: int,
                 price: float,
                 value: float
                 ) -> None:
        self.symbol = symbol
        self.side = side
        self.qty = qty
        self.price = price
        self.value = value


class PositionNotification:
    def __init__(self,
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
    def __init__(self) -> None:
        self.cash = 0.0
        self.equity_prev = 0.0
        self.equity_cur = 0.0
        self.equity_pl = 0.0

        self.trades: List[TradeNotification] = []
        self.positions: List[PositionNotification] = []

    def addPosition(self,
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
        self.positions.append(PositionNotification(
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
        ))

    def addTrade(self,
                 symbol: str,
                 side: str,
                 qty: int,
                 price: float,
                 value: float
                 ) -> None:
        self.trades.append(TradeNotification(
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            value=value
        ))


class NotifyKeys:
    class Portfolio:
        START = "portfolio_start"
        CUR = "portfolio_cur"
        PL = "portfolio_pl"

    TRADES = "trades"

    class Trade:
        Symbol = "symbol"
        Side = "side"
        Qty = "qty"
        Price = "price"
        Value = "value"

    POSITIONS = "positions"

    class Position:
        Symbol = "symbol"
        Qty = "qty"
        PL = "pl"
        Price = "price"
        Value = "value"
        PurchaseValue = "p_value"
        PurchaseDate = "p_date"
        StopPrice = "stop_price"
        LastStop = "last_stop"
        NextStop = "next_stop"


class Notifier:
    def update(self, n: Notification):
        raise NotImplementedError
