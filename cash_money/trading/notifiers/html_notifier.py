from .notfier import Notifier
from .html_generator import HTMLGen

class HTMLNotifier(Notifier):
    def __init__(self):
        self.gen = HTMLGen()

    def update(self, portfolio_start, portfolio_cur, portfolio_pl, trades, positions):
        content = self.gen.generate(portfolio_start, portfolio_cur, portfolio_pl, trades, positions)
        # TODO