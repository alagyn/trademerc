from jinja2 import Environment, FileSystemLoader, select_autoescape
from .notfier import NotifyKeys

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
