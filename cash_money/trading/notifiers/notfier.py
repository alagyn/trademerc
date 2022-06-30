from abc import ABC

class Notifier(ABC):
    def update(self, portfolio_start, portfolio_cur, portfolio_pl, trades, positions):
        raise NotImplementedError
