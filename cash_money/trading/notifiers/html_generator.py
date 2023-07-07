from jinja2 import Environment, FileSystemLoader, select_autoescape

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


class HTMLGen:
    def __init__(self):
        self.htmlEnv = Environment(
            loader=FileSystemLoader('html_templates'),
            autoescape=select_autoescape()
        )
        self.emailTemplate = self.htmlEnv.get_template("emailtemplate.html")

    def generate(self, portfolio_start, portfolio_cur, portfolio_pl, trades, positions):
        args = {
            NotifyKeys.Portfolio.START: portfolio_start,
            NotifyKeys.Portfolio.CUR: portfolio_cur,
            NotifyKeys.Portfolio.PL: portfolio_pl,
            NotifyKeys.TRADES: trades,
            NotifyKeys.POSITIONS: positions
        }
        return self.emailTemplate.render(
            **args
        )
