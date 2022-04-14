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


class Trader:
    def __init__(self, strats: Dict[str, Strategy], broker: Broker):

        self.broker = broker

        # TODO check for proper shutdown
        # setup initial buying power
        self.totalBuyPwr = 0
        self.updateBuyPwr()

        # Dict of symb->strat
        self.strats = strats

        setupTime = max([x.getSetupTime() for x in strats.values()])

        setupBars = broker.getSetupBars(setupTime)

        # Setup Indicators
        for sym, strat in strats.items():
            strat.setupIndicators(setupBars[sym])


    def trade(self):
        # Update indicators with today's values
        logInfo('Updating Indicators')
        self.updateIndicators()

        # Update positions and BP
        logInfo('Updating Positions')
        self.updateBuyPwr()

        # Calculate today's actions
        logInfo('Calculating Daily Actions')
        actions = self.getDailyActions()

        # Run actions
        logInfo('Running Daily Actions')
        self.runActions(actions)

    def updateIndicators(self):
        for sym, stk in self.broker.stocks.items():
            self.strats[sym].addData(stk.bar)

    def updateBuyPwr(self):
        self.totalBuyPwr = round(self.broker.buyPwr() * BUY_PWR_SAFETY, 2)

    def getDailyActions(self) -> List[Action]:
        actions = []
        for sym, strat in self.strats.items():
            stk = self.broker.stocks[sym]
            actions.append(strat.nextAction(self.broker.tradeDay, stk))

        return actions

    def runActions(self, actions: List[Action]):
        numOutOfMarket = 0
        for sym, stock in self.broker.stocks.items():
            if stock.status() == StockStatus.OutMarket:
                numOutOfMarket += 1

        buyPwr = self.totalBuyPwr / numOutOfMarket

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
        qty = calcQty(buyPwr, action.stock.bar.c)

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
