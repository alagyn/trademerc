from ..events import CMEventListener, EndOfTradeStepEvent, Notification
from .html_generator import HTMLGen


class HTMLNotifier(CMEventListener):
    def __init__(self):
        self.gen = HTMLGen()

    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        #content = self.gen.generate(portfolio_start, portfolio_cur, portfolio_pl, trades, positions)
        # TODO
        pass
