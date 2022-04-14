import logging
from typing import Union, Tuple, Dict, List
import numpy as np
import math

import cmErrors
from objects.bar import Bar
from objects.order import Order, OrderType, OrderStatus
from objects.position import Position
from objects.stock import Stock
from .broker import Broker


class BacktestOrder(Order):
    _ID_GEN = 0

    def __init__(self, orderT: OrderType, symbol: str, qty: int, price: float,
                 stopLimit: Union[Tuple[float, float], None] = None):
        super().__init__(BacktestOrder._ID_GEN)
        BacktestOrder._ID_GEN += 1

        self.stat = OrderStatus.UNFILLED
        self.price = price
        self._sym = symbol
        self._qty = qty
        self._orderType = orderT
        self._sl = stopLimit

    def status(self) -> OrderStatus:
        return self.stat

    def orderType(self) -> OrderType:
        pass

    def symbol(self) -> str:
        return self._sym

    def qty(self) -> Union[int, None]:
        return self._qty

    def filledQty(self) -> int:
        if self.stat == OrderStatus.FILLED:
            return self._qty
        else:
            return 0

    def filledAvgPrice(self) -> float:
        return self.price

    def stopPrice(self) -> Union[float, None]:
        return self._sl[0]

    def limitPrice(self) -> Union[float, None]:
        return self._sl[1]


class Stats:
    def __init__(self):
        self.startingVal = 0
        self.lossList = []
        self.winList = []

        self.buyDays = []
        self.buyPrices = []

        self.sellDays = []
        self.sellPrices = []
        self.sellDeltas = []

    def addBuy(self, day, value, unitCost):
        self.startingVal = value
        self.buyDays.append(day)
        self.buyPrices.append(unitCost)

    def addSell(self, day, value, unitSell):
        delta = value - self.startingVal
        self.sellDays.append(day)
        self.sellPrices.append(unitSell)
        self.sellDeltas.append(delta)

        if delta < 0:
            self.lossList.append(delta)
        else:
            self.winList.append(delta)


def logInfo(m: str):
    logging.info(f"Backtest: {m}")


def checkStop(stop):
    if stop < 0:
        raise cmErrors.BacktestError(f'Stop Price Below zero: ${stop:.2f}')


def calcSQN(tradeList) -> float:
    """
    Calculates the System Quality Number
    Should be reliable if stats.numTrades >= 3.0
    """

    arr = np.array(tradeList)

    a = math.sqrt(len(tradeList))
    # avg profit
    b = np.average(arr)
    # profit std
    c = np.std(arr)

    return a * b / c


class BacktestBroker(Broker):
    def __init__(self, startingValue: float, symbols: List[str], bars: Dict[str, List[Bar]], dates, startIdx: int,
                 endIdx: int):
        super().__init__(symbols)

        self.startingVal = startingValue
        self.totalCash = startingValue

        self.qty = {}
        self.stats = {}
        self.stops = {}

        for sym in self.symbols:
            self.qty[sym] = 0
            self.stats[sym] = Stats()

        self.bars = bars
        self.dates = dates
        self.startIdx = startIdx
        self.tradeIdx = startIdx
        self.endTradeIdx = endIdx
        self.runtime = endIdx - startIdx

        self.portfolio_cash = np.array([0.0] * self.runtime)
        self.portfolio_value = np.array([0.0] * self.runtime)

        self.curDate = "INIT"
        self.datekey = symbols[0]

    def preRun(self):
        pass

    def preTrade(self) -> bool:
        if self.tradeIdx >= self.endTradeIdx:
            return False

        logInfo(f"Begin Trade Day: {self.tradeDay}")

        self.curDate = self.dates[self.tradeIdx]

        # Update bars and check stops
        for sym in self.symbols:
            self.stocks[sym].updateBar(self.bars[sym][self.tradeIdx])
            if sym in self.stops and self.stops[sym] > self.bars[sym][self.tradeIdx].lo:
                logInfo(f"\t{sym}: Stop Activated")
                newCash = self.qty[sym] * self.stops[sym]
                self.totalCash += newCash

                self.stats[sym].addSell(self.curDate, newCash, self.stops[sym])

                self.qty[sym] = 0
                self.stops.pop(sym)
                self.stocks[sym].position = None

    def postTrade(self) -> None:
        if self.totalCash < 0:
            raise cmErrors.BacktestError('Negative Buy Power, Strategy Failure?')

        inMarketEquity = 0
        for sym in self.symbols:
            if self.qty[sym] > 0:
                inMarketEquity += self.qty[sym] * self.stocks[sym].bar.close

        # Update Graph Logs
        self.portfolio_cash[self.tradeDay] = round(self.totalCash, 2)
        self.portfolio_value[self.tradeDay] = round(inMarketEquity, 2)
        logInfo(f"\tTotal Value: ${self.totalCash + inMarketEquity: .2f}")

        self.tradeIdx += 1

    def postRun(self) -> None:
        # clear out any remaining positions
        for sym, q in self.qty.items():
            if q > 0:
                sellPrice = self.bars[sym][-1].close
                newCash = q * sellPrice
                self.stats[sym].addSell(self.curDate, newCash, sellPrice)
                self.totalCash += newCash

    def buyPwr(self) -> float:
        return self.totalCash

    def getSetupBars(self, setupTime: int) -> Dict[str, List[Bar]]:
        return self.bars[0:self.startIdx]

    def cancelAllOrders(self) -> None:
        pass

    def closeAllPositions(self) -> None:
        pass

    def getOrder(self, orderid: int) -> Order:
        pass

    def getAllOrders(self) -> List[Order]:
        pass

    def getPosition(self, symbol: str) -> Position:
        pass

    def getOpenPositions(self) -> Dict[str, Position]:
        pass

    def submitBuy(self, stock: Stock, qty: int, stopLimit: Union[Tuple[float, float], None] = None) -> None:
        # Set position to non-None
        stock.position = "InMarket"
        # Set new stop
        checkStop(stopLimit[0])
        self.stops[stock.symbol] = stopLimit[0]
        # update qty
        self.qty[stock.symbol] = qty
        # Update value
        trueCost = qty * stock.bar.close

        self.stats[stock.symbol].addBuy(self.curDate, trueCost, stock.bar.close)

        self.totalCash -= trueCost

    def closePosition(self, stock: Stock) -> None:
        sym = stock.symbol
        # Clear position
        stock.position = None
        # Clear stop
        self.stops.pop(sym)
        # Update value
        soldValue = self.qty[sym] * stock.bar.close
        self.totalCash += soldValue

        self.qty[sym] = 0
        # Update win/loss
        self.stats[sym].addSell(self.curDate, soldValue, stock.bar.close)

    def submitSell(self, symbol: str, qty: int) -> Order:
        pass

    def submitUpdateStop(self, stock: Stock, stopLimit: Union[Tuple[float, float], None]) -> None:
        checkStop(stopLimit[0])
        self.stops[stock.symbol] = stopLimit[0]

    def getStats(self) -> Dict[str, any]:
        wins = 0
        losses = 0
        winTotal = 0
        lossTotal = 0

        tradeList = []

        for sym, stat in self.stats.items():
            wins += len(stat.winList)
            losses += len(stat.lossList)
            winTotal += sum(stat.winList)
            lossTotal += sum(stat.lossList)

            tradeList.extend(stat.winList)
            tradeList.extend(stat.lossList)

        numTrades = len(tradeList)
        profit = self.totalCash - self.startingVal
        percentGain = profit / self.startingVal

        sqnVal = 0 if numTrades <= 1 else calcSQN(tradeList)
        wlRatio = 1 if losses == 0 else wins / losses
        avgGain = 0 if wins == 0 else winTotal / wins
        avgLoss = 0 if losses == 0 else lossTotal / losses

        winPercent = 0 if numTrades == 0 else wins / (wins + losses)

        print(f'Start Value: ${self.startingVal:.2f}, End Value: ${self.totalCash:.2f}')
        print(f'Profit: {profit:.2f}, Percent Gain: {percentGain:.2%}')
        print(f'Trades: {numTrades}, Wins: {wins}, Losses: {losses}, W/L: {wlRatio:.2f}')
        print(f'Win %: {winPercent:.2%}')
        print(f'Avg Gain: ${avgGain:.2f}')
        print(f'Avg Loss: ${avgLoss:.2f}')
        print(f'SQN: {sqnVal:.3f}')

        return {
            'StartValue': self.startingVal,
            'EndValue': round(self.totalCash, 2),
            'Profit': round(profit, 2),
            'PercentGain': round(percentGain, 4),
            'SQN': round(sqnVal, 4),
            'trades': numTrades,
            'wins': wins,
            'losses': losses,
            'wl': round(wlRatio, 2),
            'winPerc': round(winPercent, 2),
            'avgGain': round(avgGain, 2),
            'avgLoss': round(avgLoss, 2)
        }
