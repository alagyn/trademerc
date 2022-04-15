import logging
from typing import Dict, List

import math

import cmErrors
from strategies.strategy import *
from objects.stock import *
from trading.brokers.broker import Broker



BUY_PWR_SAFETY = 0.985


def calcQty(buyPwr: float, cost: float):
    return math.floor(buyPwr / cost)


def logInfo(m: str):
    logging.info(f'Trader: {m}')

def logCrit(m: str):
    logging.critical(f"Trader: {m}")

def logDebug(m: str):
    logging.debug(f"Trader: {m}")


class Trader:
    def __init__(self, strats: Dict[str, Strategy], broker: Broker):

        self.broker = broker

        # setup initial buying power
        self.totalBuyPwr = 0
        self.updateBuyPwr()

        # Dict of symb->strat
        self.strats = strats


    def trade(self):
        # Update indicators with today's values
        logDebug('Updating Indicators')
        self.updateIndicators()

        # Update positions and BP
        logDebug('Updating Positions')
        self.updateBuyPwr()

        # Calculate today's actions
        logDebug('Calculating Daily Actions')
        actions = self.getDailyActions()

        # Run actions
        logDebug('Running Daily Actions')
        self.runActions(actions)

    def updateIndicators(self):
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

        for a in actions:
            if a.action == ActionEnum.Buy:
                self.submitBuy(a, buyPwr)
            elif a.action == ActionEnum.BuyAndStop:
                self.submitBuyAndStop(a, buyPwr)
            elif a.action == ActionEnum.Sell:
                self.submitSell(a)
            elif a.action == ActionEnum.UpdateStop:
                self.submitUpdateStop(a)
            elif a.action == ActionEnum.Hold:
                # ILB
                pass

            logInfo(str(a))

    def submitBuy(self, action: Action, buyPwr):
        qty = calcQty(buyPwr, action.stock.bar.c)
        self.broker.submitBuy(action.stock, qty)

    def submitBuyAndStop(self, action: Action, buyPwr):
        qty = calcQty(buyPwr, action.stock.bar.close)

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
