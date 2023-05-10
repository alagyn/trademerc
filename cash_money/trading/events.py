from cash_money.trading.objects import Action, Bar, Order, CMPosition


class ActionEvent:

    def __init__(self, action: Action) -> None:
        self.action = action


class OrderEvent:

    def __init__(self, order: Order) -> None:
        self.order = order


class EndOfTradeStepEvent:
    pass


class PositionUpdateEvent:

    def __init__(self, position: CMPosition) -> None:
        self.position = position


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

    def onOrder(self, event: OrderEvent):
        pass

    def onPositionUpdate(self, event: PositionUpdateEvent):
        pass

    def onStockUpdate(self, event: StockUpdateEvent):
        pass

    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        pass