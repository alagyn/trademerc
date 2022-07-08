from typing import Dict, List

import math

from cash_money import cmErrors
from cash_money.trading.nodeStrategy import NodeStrategy
from cash_money.trading.brokers.broker import Broker
from cash_money.objects.action import ActionEnum, Action
from cash_money.objects.stock import StockStatus
from cash_money.utils.log_utils import logInfo as _logInfo, logErr, logDbg

BUY_PWR_SAFETY = 0.985


def calcQty(buyPwr: float, cost: float):
    return math.floor(buyPwr / cost)


def logInfo(m):
    _logInfo('Trader', m)


def logCrit(m):
    logErr('Trader', m)


def logDebug(m):
    logDbg("Trader", m)


class Trader:
    def __init__(self, strats: Dict[str, NodeStrategy], broker: Broker):

        self.broker = broker

        # setup initial buying power
        self.totalBuyPwr = 0
        self.updateBuyPwr()

        # Dict of symb->strat
        self.strats = strats

    def trade(self):
        # Update indicators with today's values
        logDebug('Updating Graphs')
        self.updateGraphs()

        # Update positions and BP
        logDebug('Updating Positions')
        self.updateBuyPwr()
        logInfo(f"Cycle Buy Power: ${self.totalBuyPwr}")

        # Calculate today's actions
        logDebug('Calculating Daily Actions')
        actions = self.getDailyActions()

        # Run actions
        logDebug('Running Daily Actions')
        self.runActions(actions)

    def updateGraphs(self):
        for sym, strat in self.strats.items():
            strat.addData(self.broker[sym].bar)

    def updateBuyPwr(self):
        self.totalBuyPwr = round(self.broker.buyPwr() * BUY_PWR_SAFETY, 2)

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

        if numOutOfMarket > 0:
            buyPwr = self.totalBuyPwr / numOutOfMarket
        else:
            buyPwr = 0

        logInfo(f"Num out of market: {numOutOfMarket}, per-stock buy pwr: ${buyPwr:.2f}")

        for a in actions:
            if a.action == ActionEnum.Buy:
                if buyPwr <= 0:
                    logInfo(f"Buy Power is <= 0: ${buyPwr:.2f}, skipping:\n\t{str(a)}")
                    continue
                self.submitBuy(a, buyPwr)
            elif a.action == ActionEnum.BuyAndStop:
                if buyPwr <= 0:
                    logInfo(f"Buy Power is <= 0: ${buyPwr:.2f}, skipping:\n\t{str(a)}")
                    continue
                self.submitBuyAndStop(a, buyPwr)
            elif a.action == ActionEnum.Sell:
                self.submitSell(a)
            elif a.action == ActionEnum.UpdateStop:
                self.submitUpdateStop(a)
            elif a.action == ActionEnum.HoldInMarket or a.action == ActionEnum.HoldOutMarket:
                # ILB
                pass

            logInfo(str(a))

    def submitBuy(self, action: Action, buyPwr):
        qty = calcQty(buyPwr, action.stock.bar.close)
        if qty <= 0:
            logInfo(f"Qty <= 0: {qty}, not submitting Buy request\n\t{str(action)}")
            return
        self.broker.submitBuy(action.stock, qty)

    def submitBuyAndStop(self, action: Action, buyPwr):
        qty = calcQty(buyPwr, action.stock.bar.close)
        if qty <= 0:
            logInfo(f"Qty <= 0: {qty}, not submitting Buy&Stop request\n\t{str(action)}")
            return

        try:
            self.broker.submitBuy(action.stock, qty,
                                  (action.args['stopPrice'], action.args['limitPrice']))
        except KeyError as err:
            raise cmErrors.ActionError(f'Action missing argument: "{str(err)}", Action: {str(action)}')

    def submitSell(self, action: Action):
        self.broker.closePosition(action.stock)

    def submitUpdateStop(self, action: Action):
        try:
            if action.stock.stopOrder is None:
                raise cmErrors.ActionError('Cannot Update stop, no stop created')

            self.broker.submitUpdateStop(action.stock,
                                         (action.args['stopPrice'], action.args['limitPrice']))
        except KeyError as err:
            raise cmErrors.ActionError(f'Action missing argument: "{str(err)}", Action: {str(action)}')
