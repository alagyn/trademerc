from abc import ABC


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


class Notifier(ABC):
    def update(self, portfolio_start, portfolio_cur, portfolio_pl, trades, positions):
        raise NotImplementedError
