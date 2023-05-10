from typing import List, Dict, Optional, Any
import math
import datetime

from cash_money import cmErrors
from cash_money.trading.nodeStrategy import NodeStrategy
from cash_money.trading.objects import ActionEnum, Action, BuyAction, UpdateStopAction, StockStatus
from cash_money.trading.objects import Order, Stock
from cash_money.trading.events import *
import logging
from cash_money.utils.date_utils import deltaBusinessDays

BUY_PWR_SAFETY = 0.985


def calcQty(buyPwr: float, cost: float):
    return math.floor(buyPwr / cost)


log = logging.getLogger("Trader")

MAX_DAY_TRADES = 3


class Trader:
    """
    Abstract class with the non-broker specific logic
    """

    def __init__(self, strats: Dict[str, NodeStrategy]):

        # setup initial buying power
        self.buying_power = 0
        self.updateBuyPower()

        # Dict of symb->strat
        self.strats = strats

        self.tradeStep = 0

        # This should be using the US market time, ES
        # UTC-5, or UTC-4 for Daylight savings time
        # values are provided by the broker
        self.lastUpdateTime = self.curDateTime = self.now()

        # Total amount of unsettled funds
        self.totalUnsettled = 0
        # Total number of day trades in the last 5 days
        self.totalDayTrades = 0

        self.listeners: List[CMEventListener] = []

        self.symbols = strats.keys()
        # Dict of symb->stock
        self.stocks: Dict[str, Stock] = {
            x: Stock(x)
            for x in self.symbols
        }

    def incStep(self):
        self.tradeStep += 1

    def addListener(self, listener: CMEventListener):
        self.listeners.append(listener)

    def trade(self):
        # Update the trader's time
        self.curDateTime = self.now()

        # Update stock queues
        self.updateStocks()

        # Update indicators with today's values
        log.debug('Updating Graphs')
        self.updateGraphs()

        # Update positions and BP
        log.debug('Updating Positions')
        self.updateBuyPower()
        log.info(f"Cycle Cash: ${self.cash}")

        # Calculate today's actions
        log.debug('Calculating Daily Actions')
        actions = self.getStepActions()

        # Run actions
        log.info('Running Actions')
        self.runActions(actions)
        self.notifyEndOfTradeStep()

    def notifyEndOfTradeStep(self):
        event = EndOfTradeStepEvent()
        for x in self.listeners:
            x.onEndOfTradeStep(event)

    def notifyAction(self, action: Action):
        event = ActionEvent(action)
        for x in self.listeners:
            x.onAction(event)

    def notifyStockUpdate(self, symbol: str, bar: Bar):
        event = StockUpdateEvent(symbol, bar)
        for x in self.listeners:
            x.onStockUpdate(event)

    def notifyOrderEvent(self, order):
        event = OrderEvent(order)
        for x in self.listeners:
            x.onOrder(event)

    def notifyPositionUpdate(self, position):
        event = PositionUpdateEvent(position)
        for x in self.listeners:
            x.onPositionUpdate(event)

    def updateStocks(self):
        """
        Updates each stock using the cur date.
        Append a new entry to daytrade and unsettled fund queues
        for each business day that has passed since the last update
        It's up to the broker to set these values so that they use
        the most accurate amounts
        Recalculates totalUnsettled and totalDayTrades
        """
        bDays = deltaBusinessDays(self.lastUpdateTime, self.curDateTime)
        if bDays == 0:
            return

        self.totalUnsettled = 0
        self.totalDayTrades = 0

        for stock in self.stocks.values():
            for i in range(bDays):
                # Add a new entry to drop off old ones
                stock.unsettledFunds.append(0)
                stock.dayTrades.append(0)
            # Update totals
            self.totalUnsettled += sum(stock.unsettledFunds)
            self.totalDayTrades += sum(stock.dayTrades)

        # Update the lastUpdateTime to be now
        self.lastUpdateTime = self.curDateTime

    def updateGraphs(self):
        for sym, strat in self.strats.items():
            bar = self.stocks[sym].bar
            if bar is not None:
                strat.addData(bar)

    def updateBuyPower(self):
        self.buying_power = round(self.cash() * BUY_PWR_SAFETY, 2)

    def getStepActions(self) -> List[Action]:
        actions = []
        for sym, strat in self.strats.items():
            stk = self.stocks[sym]
            actions.append(strat.nextAction(self.tradeStep, stk))

        return actions

    def runActions(self, actions: List[Action]):
        numOutOfMarket = 0
        for stock in self.stocks.values():
            if stock.status() == StockStatus.OutMarket:
                numOutOfMarket += 1

        usableCash = self.buying_power - self.totalUnsettled

        if numOutOfMarket > 0:
            buyPwr = usableCash / numOutOfMarket
        else:
            buyPwr = 0.0

        log.info(
            f"Unsettled Funds: ${self.totalUnsettled:.2f}, usable cash: ${usableCash:.2f}"
        )
        log.info(
            f"Num out of market: {numOutOfMarket}, per-stock cash: ${buyPwr:.2f}"
        )
        log.info(f"Unsettled Day trades: {self.totalDayTrades}")

        for a in actions:
            log.debug(
                "\tSymbol: %s, Action: %s", a.stock.symbol, a.action.name
            )

            if a.action == ActionEnum.Buy:
                if buyPwr <= 0:
                    log.info(f"\t\tBuy Power is <= 0: ${buyPwr:.2f}, skipping")
                    continue
                self._submitBuy(a, buyPwr)
            elif a.action == ActionEnum.Sell:
                self._submitSell(a)
            elif a.action == ActionEnum.UpdateStop:
                self._submitUpdateStop(a)
            elif a.action == ActionEnum.HoldInMarket or a.action == ActionEnum.HoldOutMarket:
                # ILB
                pass

            self.notifyAction(a)

    def _submitBuy(self, action: Action, buyPwr):
        if not isinstance(action, BuyAction):
            raise cmErrors.ActionError("Action not a BuyAction")

        if action.stock.bar is None:
            raise cmErrors.ActionError("Stock bar is None")

        qty = calcQty(buyPwr, action.stock.bar.close)
        if qty <= 0:
            log.info(
                f"Qty <= 0: {qty}, not submitting Buy request:\n\t{str(action)}"
            )
            return

        self.submitBuy(action.stock, qty, action.stopPrice)

    def _submitSell(self, action: Action):
        if action.stock.position is None:
            raise RuntimeError()

        if action.stock.buyDate is None:
            raise RuntimeError()

        if action.stock.buyDate == self.curDateTime:
            if self.totalDayTrades >= MAX_DAY_TRADES:
                log.info("Ignoring Sell, sell would go above max day trades")
                return

            action.stock.dayTrades[-1] += 1
            self.totalDayTrades += 1

        self.closePosition(action.stock)

    def _submitUpdateStop(self, action: Action):
        if not isinstance(action, UpdateStopAction):
            raise cmErrors.ActionError("Action not an UpdateStopAction")

        o = action.stock.stopOrder
        if o is None:
            raise cmErrors.ActionError(
                f'Cannot Update stop, no stop order created:\n\t{action}'
            )

        oldPrice = o.stopPrice()
        if oldPrice is None:
            raise cmErrors.ActionError(
                f'Cannot Update stop, no invalid stop order:\n\t{action}'
            )

        if action.stopPrice == oldPrice:
            log.info(f"Ignoring {action}, stop-price is equal")
            return

        self.submitUpdateStop(action.stock, action.stopPrice)

    ## ABSTRACT FUNCTIONS

    def now(self) -> datetime.date:
        """
        Return a datetime representing the current time as of trading
        """
        raise NotImplementedError

    def preRun(self):
        """
        Called once before any trades occur
        :return:
        """
        raise NotImplementedError

    def preTrade(self) -> bool:
        """
        Called before the trader is run, all relevant data is updated for the trader to use
        In particular, positions and stock bars should be updated
        :return: true if run should continue, else false
        """
        raise NotImplementedError

    def postTrade(self) -> None:
        """
        Called after the trader is run
        :return: None
        """
        raise NotImplementedError

    def postRun(self) -> None:
        """
        Called once after run is complete, prior to exit
        :return: None
        """
        raise NotImplementedError

    def cash(self) -> float:
        """
        Returns the account's current cash value
        :return: the buying power
        """
        raise NotImplementedError

    def cancelAllOrders(self) -> None:
        """
        Cancels all unfilled orders
        :return: None
        """
        raise NotImplementedError

    def closeAllPositions(self) -> None:
        """
        Closes all open positions
        :return: None
        """
        raise NotImplementedError

    def getOrder(self, orderid: int) -> Order:
        """
        Returns the order for the given id
        :param orderid: The order's id
        :return: The order
        """
        raise NotImplementedError

    def getAllOrders(self) -> List[Order]:
        """
        Returns a list of all open orders
        :return: The orders
        """
        raise NotImplementedError

    def getOpenPositions(self) -> Dict[str, Any]:
        """
        Returns a dict of all open positions
        :return: the positions
        """
        raise NotImplementedError

    def submitBuy(
        self,
        stock: Stock,
        qty: int,
        stopLoss: Optional[float] = None
    ) -> None:
        """
        Submits a buy order for the given symbol and quantity
        :param stock: The stock to buy
        :param qty: The quantity to buy
        :param stopLimit: An optional tuple to place a stop-limit order [stop, limit]
        :return: The new order
        """
        raise NotImplementedError

    def closePosition(self, stock: Stock) -> None:
        """
        Closes a position and sells all shares at current market price
        :param stock: The stock
        :return: None
        """
        raise NotImplementedError

    def submitSell(self, stock: Stock, qty: int) -> Order:
        """
        Sumbits a sell order for the given symbol and quantity
        :param stock: The stock
        :param qty: The quantity
        :return: The sell order
        """
        raise NotImplementedError

    def submitUpdateStop(self, stock: Stock, stopPrice: float) -> None:
        """
        Replaces an existing stop order
        :param stock: The stock
        :param stopLimit: A tuple to place a stop-limit order [stop, limit]
        :return: The new order
        """
        raise NotImplementedError
