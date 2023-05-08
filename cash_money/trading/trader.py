from typing import Dict, List

import math

from cash_money import cmErrors
from cash_money.trading.nodeStrategy import NodeStrategy
from cash_money.trading.brokers.broker import Broker
from cash_money.objects import ActionEnum, Action, BuyAction, UpdateStopAction, StockStatus
import logging
from cash_money.utils.date_utils import deltaBusinessDays

BUY_PWR_SAFETY = 0.985


def calcQty(buyPwr: float, cost: float):
    return math.floor(buyPwr / cost)


log = logging.getLogger("Trader")

MAX_DAY_TRADES = 3


class Trader:

    def __init__(self, strats: Dict[str, NodeStrategy], broker: Broker):

        self.broker = broker

        # setup initial buying power
        self.cash = 0
        self.updateCash()

        # Dict of symb->strat
        self.strats = strats

        # This should be using the US market time, ES
        # UTC-5, or UTC-4 for Daylight savings time
        # values are provided by the broker
        self.lastUpdateTime = self.curDateTime = broker.now()

        # Total amount of unsettled funds
        self.totalUnsettled = 0
        # Total number of day trades in the last 5 days
        self.totalDayTrades = 0

    def trade(self):
        # Update the trader's time
        self.curDateTime = self.broker.now()

        # Update stock queues
        self.updateStocks()

        # Update indicators with today's values
        log.debug('Updating Graphs')
        self.updateGraphs()

        # Update positions and BP
        log.debug('Updating Positions')
        self.updateCash()
        log.info(f"Cycle Cash: ${self.cash}")

        # Calculate today's actions
        log.debug('Calculating Daily Actions')
        actions = self.getDailyActions()

        # Run actions
        log.debug('Running Daily Actions')
        self.runActions(actions)

    def updateStocks(self):
        """
        Updates each stock usng the cur date.
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

        for stock in self.broker:
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
            bar = self.broker[sym].bar
            if bar is not None:
                strat.addData(bar)

    def updateCash(self):
        self.cash = round(self.broker.cash() * BUY_PWR_SAFETY, 2)

    def getDailyActions(self) -> List[Action]:
        actions = []
        for sym, strat in self.strats.items():
            stk = self.broker[sym]
            actions.append(strat.nextAction(self.broker.tradeDay, stk))

        return actions

    def runActions(self, actions: List[Action]):
        numOutOfMarket = 0
        for stock in self.broker:
            if stock.status() == StockStatus.OutMarket:
                numOutOfMarket += 1

        usableCash = self.cash - self.totalUnsettled

        if numOutOfMarket > 0:
            buyPwr = usableCash / numOutOfMarket
        else:
            buyPwr = 0

        log.info(
            f"Unsettled Funds: ${self.totalUnsettled:.2f}, usable cash: ${usableCash:.2f}"
        )
        log.info(
            f"Num out of market: {numOutOfMarket}, per-stock cash: ${buyPwr:.2f}"
        )
        log.info(f"Unsettled Day trades: {self.totalDayTrades}")

        for a in actions:
            if a.action == ActionEnum.Buy:
                if buyPwr <= 0:
                    log.info(f"\t\tBuy Power is <= 0: ${buyPwr:.2f}, skipping")
                    continue
                self.submitBuy(a, buyPwr)
            elif a.action == ActionEnum.Sell:
                self.submitSell(a)
            elif a.action == ActionEnum.UpdateStop:
                self.submitUpdateStop(a)
            elif a.action == ActionEnum.HoldInMarket or a.action == ActionEnum.HoldOutMarket:
                # ILB
                pass

    def submitBuy(self, action: Action, buyPwr):
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

        self.broker.submitBuy(action.stock, qty, action.stop_limit)

    def submitSell(self, action: Action):
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

        self.broker.closePosition(action.stock)

    def submitUpdateStop(self, action: Action):
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

        if action.stop_limit == oldPrice:
            log.info(f"Ignoring {action}, stop-limit is equal")
            return

        self.broker.submitUpdateStop(action.stock, action.stop_limit)
