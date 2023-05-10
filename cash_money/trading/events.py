from cash_money.trading.objects import Action, Bar

class ActionEvent:
    def __init__(self, action: Action) -> None:
        self.action = action

class EndOfTradeStepEvent:
    pass

class PositionUpdateEvent:
    pass

class StockUpdateEvent:
    def __init__(self, symbol: str, bar: Bar) -> None:
        self.bar = bar
        self.symbol = symbol

class CMEventListener:
    """
    CashMoney Event Listener interface
    """

    def onAction(self, event: ActionEvent):
        pass

    def onPositionUpdate(self, event: PositionUpdateEvent):
        pass

    def onStockUpdate(self, event: StockUpdateEvent):
        pass

    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        pass