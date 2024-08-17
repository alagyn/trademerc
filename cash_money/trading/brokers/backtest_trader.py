from typing import Union, Tuple, Dict, List, Optional, Any
import numpy as np
import math
import datetime
import logging

import sys

from cash_money import cmErrors
from cash_money.trading.objects import Bar, Order, OrderType, OrderStatus, Stock, CMPosition, StockStatus
from cash_money.trading.trader import Trader
from cash_money.trading.notifiers.console_notifier import ConsoleNotifier
from cash_money.trading.events import Notification
from cash_money.utils.run_utils import BarDict
from cash_money.utils.date_utils import nextBusinessDay
from cash_money.trading.nodeStrategy import NodeStrategy

log = logging.getLogger("Backtest Brkr")


class _TradeList:

    def __init__(self):
        self._startingVal = 0
        self.lossList: List[float] = []
        self.winList: List[float] = []

        self.buyDays = []
        self.buyPrices = []

        self.sellDays = []
        self.sellPrices = []
        self.sellDeltas = []

    def addBuy(self, day, value, unitCost):
        self._startingVal = value
        self.buyDays.append(day)
        self.buyPrices.append(unitCost)

    def addSell(self, day, value, unitSell):
        delta = value - self._startingVal
        self.sellDays.append(day)
        self.sellPrices.append(unitSell)
        self.sellDeltas.append(delta)

        if delta < 0:
            self.lossList.append(delta)
        else:
            self.winList.append(delta)


class BackTestPosition(CMPosition):

    def __init__(self, symbol: str) -> None:
        self.symbol: str = symbol
        self._qty: int = 0
        self.side = ""
        self.initUnitPrice: float = 0
        self.stopPrice: Optional[float] = None
        self.purchaseDate: str = ""

        self.prevStopUpdate: str = "TODO"
        self.nextStopUpdate: str = "TODO"

        self.stats = _TradeList()

    def getstatus(self) -> StockStatus:
        # always return in market since we set the position to none otherwise
        return StockStatus.InMarket

    def data(self) -> Any:
        return None

    def qty(self):
        return self._qty

    def addNotification(self, n: Notification, bar: Bar):
        purchaseValue = self.initUnitPrice * self._qty
        value = bar.close * self.qty()
        pl = value - purchaseValue
        n.addPosition(
            symbol=self.symbol,
            qty=self._qty,
            pl=pl,
            price=bar.close,
            value=value,
            purchaseValue=purchaseValue,
            stopPrice=self.stopPrice if self.stopPrice is not None else 0,
            lastStop=self.prevStopUpdate,
            nextStop=self.nextStopUpdate,
            purchaseDate=self.purchaseDate
        )


class BacktestOrderStub(Order):
    _ID_GEN = 0

    def __init__(self, stopPrice: Optional[float]):
        super().__init__(BacktestOrderStub._ID_GEN)
        BacktestOrderStub._ID_GEN += 1

        self._sl = stopPrice

    def stopPrice(self) -> Union[float, None]:
        return self._sl


class BacktestOrder(BacktestOrderStub):

    def __init__(
        self,
        orderT: OrderType,
        symbol: str,
        qty: int,
        price: float,
        timestamp: datetime.datetime,
        stopLimit: Optional[float] = None
    ):
        super().__init__(stopLimit)
        self.stat = OrderStatus.UNFILLED
        self.price = price
        self._sym = symbol
        self._qty = qty
        self._orderType = orderT
        self._timestamp = timestamp

    def status(self) -> OrderStatus:
        return self.stat

    def orderType(self) -> OrderType:
        return self._orderType

    def symbol(self) -> str:
        return self._sym

    def qty(self) -> Union[int, None]:
        return self._qty

    def filledQty(self) -> int:
        return self._qty

    def filledAvgPrice(self) -> float:
        return self.price

    def data(self) -> Any:
        return None

    def timestamp(self) -> datetime.datetime:
        return self._timestamp


def checkStop(stop: float):
    if stop < 0:
        raise cmErrors.BacktestError(f'Stop Price Below zero: ${stop:.2f}')


def calcSQN(tradeList) -> float:
    # TODO this calculation is bad maybe?
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

    return float(a * b / c)


class BacktestStats:

    def __init__(self, startingVal: float, stat: _TradeList):

        self.wins = len(stat.winList)
        self.winValue = sum(stat.winList)
        self.losses = len(stat.lossList)
        self.lossValue = sum(stat.lossList)

        trades = stat.winList.copy()
        trades.extend(stat.lossList)
        self.trades = len(trades)

        # loss list is negative, just add
        self.profit = sum(stat.winList) + sum(stat.lossList)
        self.percGain = self.profit / startingVal
        self.sqn = 0 if self.trades <= 1 else calcSQN(trades)
        self.wlRatio = 1.0 if self.losses == 0 else self.wins / self.losses
        totalTrades = self.wins + self.losses
        self.winPerc = 1.0 if totalTrades == 0 else self.wins / totalTrades
        self.avgGain = 0 if self.wins == 0 else self.winValue / self.wins
        self.avgLoss = 0 if self.losses == 0 else self.lossValue / self.losses

    def toDict(self) -> Dict[str, str]:
        return {
            'Profit': f"{self.profit:,.2f}",
            'PercentGain': f"{self.percGain:.2%}",
            'SQN': f"{self.sqn:.3f}",
            'trades': str(self.trades),
            'wins': str(self.wins),
            'losses': str(self.losses),
            'wl': f"{self.wlRatio:.2f}",
            'winPerc': f"{self.winPerc:.2%}",
            'avgGain': f"{self.avgGain:,.2f}",
            'avgLoss': f"{self.avgLoss:,.2f}"
        }


class RunStats:

    def __init__(self, startVal: float, endVal: float, totalStats: _TradeList, symbols: Dict[str, _TradeList]) -> None:
        self.startValue = startVal
        self.endValue = endVal
        self.totalStats = BacktestStats(startVal, totalStats)
        self.symbolStats: Dict[str, BacktestStats] = {
            name: BacktestStats(startVal, stat)
            for name, stat in symbols.items()
        }


class BacktestTrader(Trader):

    def __init__(
        self,
        strats: Dict[str, NodeStrategy],
        startingValue: float,
        bars: BarDict,
    ):
        super().__init__(strats)

        if len(strats) == 0:
            raise cmErrors.CMError("Cannot backtest, no symbols provided")

        self.startingVal = startingValue
        self.totalCash = startingValue

        self.positions: Dict[str, BackTestPosition] = {
            sym: BackTestPosition(sym)
            for sym in strats.keys()
        }

        self.bars = bars
        self.barIdx = 0

        # Get the len of the bars
        for sym in self.symbols:
            self.endIdx = len(self.bars[sym])
            break

        self.runtime = self.endIdx

        self.portfolio_cash = np.array([0.0] * self.runtime)
        self.portfolio_value = np.array([0.0] * self.runtime)

        # Get the first date
        self.curDate = datetime.datetime(1, 1, 1)
        for sym, barlist in self.bars.items():
            if barlist[0] is not None:
                self.curDate = barlist[0].date
                break

        self.addListener(ConsoleNotifier())
        self._next_n = Notification(self.curDate)

        self.prevEquity = startingValue

    def preRun(self):
        pass

    def getTotalMarketValue(self) -> float:
        total = 0.0
        for stock in self.stocks.values():
            if stock.position is not None and stock.bar is not None:
                total += stock.position.qty() * stock.bar.close

        return total

    def now(self) -> datetime.date:
        return self.curDate

    def preTrade(self) -> bool:
        if self.barIdx >= self.endIdx:
            return False

        log.info(f"Begin Trade Day: {self.tradeStep}, Date: {self.curDate}")

        self.prevEquity = self.totalCash + self.getTotalMarketValue()

        # Update bars and check stops
        for sym in self.symbols:
            newBar = self.bars[sym][self.barIdx]
            self.stocks[sym].updateBar(newBar)
            if newBar is not None:
                self.notifyStockUpdate(sym, newBar)

            position = self.positions[sym]

            if position.stopPrice is not None and newBar is not None:
                if position.stopPrice > newBar.lo:
                    newCash = position.qty() * position.stopPrice
                    self.totalCash += newCash
                    position.stats.addSell(self.curDate, newCash, position.stopPrice)

                    # Make an "order" so we can notify the UI
                    o = BacktestOrder(OrderType.SELL, sym, position.qty(), position.stopPrice, self.curDate)
                    self.notifyOrderEvent(o)

                    self._next_n.addTrade(
                        symbol=sym, side="Sell", qty=position.qty(), price=position.stopPrice, value=newCash
                    )
                    # Reset position
                    position._qty = 0
                    self.stocks[sym].position = None
                    position.stopPrice = None

                    log.info(f"{sym}: Stop Activated, Value: ${newCash:.2f}")

        return True

    def postTrade(self) -> None:
        if self.totalCash < 0:
            raise cmErrors.BacktestError('BacktestBroker.postTrade() Negative Buy Power, Strategy Failure?')

        for sym, stock in self.stocks.items():
            if stock.bar is not None:
                self._next_n.addBar(sym, stock.bar)

        inMarketEquity = 0
        for sym, position in self.positions.items():
            bar = self.stocks[sym].bar
            if position.qty() > 0:
                if bar is not None:
                    inMarketEquity += position.qty() * bar.close
                else:
                    bar = Bar(0, 0, 0, 0, self.curDate)
                position.addNotification(self._next_n, bar)

        # Update Graph Logs
        self.portfolio_cash[self.tradeStep] = round(self.totalCash, 2)
        self.portfolio_value[self.tradeStep] = round(inMarketEquity, 2)

        cur_equity = self.totalCash + inMarketEquity

        self._next_n.cash = self.totalCash
        self._next_n.equity_cur = cur_equity
        self._next_n.equity_prev = self.prevEquity
        self._next_n.equity_pl = cur_equity - self.prevEquity

        self.notifyEndOfTradeStep(self._next_n)
        self._next_n = Notification(self.curDate)

        self.barIdx += 1
        self.curDate = nextBusinessDay(self.curDate)

    def postRun(self) -> None:
        # clear out any remaining positions
        log.info("Closing open positions")
        for sym, position in self.positions.items():
            if position.qty() > 0:
                sellPrice = -1
                for x in reversed(self.bars[sym]):
                    if x is None:
                        continue
                    sellPrice = x.close
                    break

                if sellPrice < 0:
                    raise RuntimeError("No Bars???????????")

                newCash = position.qty() * sellPrice
                position.stats.addSell(self.curDate, newCash, sellPrice)
                self.totalCash += newCash
                log.info(f"    [{sym}] Qty: {position.qty()}, Value: ${newCash:.2f}")

                o = BacktestOrder(OrderType.SELL, sym, position.qty(), sellPrice, self.curDate)
                self.notifyOrderEvent(o)

    def cash(self) -> float:
        return self.totalCash

    def cancelAllOrders(self) -> None:
        # TODO
        raise NotImplementedError

    def getOrder(self, orderid: int) -> Order:
        # TODO
        raise NotImplementedError

    def getAllOrders(self) -> List[Order]:
        # TODO
        raise NotImplementedError

    def getPosition(self, symbol: str) -> Any:
        # TODO
        raise NotImplementedError

    def getOpenPositions(self) -> Dict[str, Any]:
        # TODO
        raise NotImplementedError

    def submitBuy(self, stock: Stock, qty: int, stopLimit: Optional[float] = None) -> None:
        if stock.bar is None:
            log.warn(f"Cannot submit buy for {stock.symbol}, bar is none")
            return

        # Set position to non-None
        stock.position = self.positions[stock.symbol]
        if stopLimit is not None:
            # Set new stop
            checkStop(stopLimit)
            stock.position.stopPrice = stopLimit
            t = OrderType.BUY
            stock.stopOrder = BacktestOrderStub(stopLimit)
        else:
            t = OrderType.BUY

        # update qty
        stock.position._qty = qty
        # Update value
        trueCost = qty * stock.bar.close

        if trueCost > self.totalCash:
            newQty = int(self.totalCash // stock.bar.close)
            log.warn(
                f"Attempted to buy more than we can afford\n"
                f"symbol: {stock.symbol}, qty: {qty}, price: ${stock.bar.close:.2f}, value: ${stock.bar.close * qty:.2f}\n"
                f"Quantity actually bought: {newQty}, value: ${stock.bar.close * newQty:.2f}"
            )
            qty = newQty

        stock.position.stats.addBuy(self.curDate, trueCost, stock.bar.close)

        self.totalCash -= trueCost

        o = BacktestOrder(t, stock.symbol, qty, stock.bar.close, self.curDate, stopLimit)
        stock.buyOrder = o
        stock.buyDate = self.curDate

        self._next_n.addTrade(
            symbol=stock.symbol, side="Buy", qty=qty, price=stock.bar.close, value=stock.bar.close * qty
        )

        self.notifyOrderEvent(o)

    def closePosition(self, stock: Stock) -> None:
        if stock.position is not None:
            self.submitSell(stock, stock.position.qty())
        else:
            log.warn(f"Cannot close position for {stock.symbol}, no position open")

    def closeAllPositions(self) -> None:
        for stock in self.stocks.values():
            if stock.position is not None and stock.position.qty() > 0:
                self.closePosition(stock)

    def submitSell(self, stock: Stock, qty: int) -> None:
        if stock.bar is None:
            log.warn(f"Cannot submit sell for {stock.symbol}, bar is None")
            raise RuntimeError()

        if stock.position is None:
            log.warn(f"Cannot submit sell for {stock.symbol}, no position open")
            return

        if not isinstance(stock.position, BackTestPosition):
            return

        position: BackTestPosition = stock.position
        if qty >= position.qty():
            if qty > position.qty():
                log.warn(
                    f"Attempted sell more shares than we own, closing position: attempted: {qty}, owned: {position.qty}"
                )
                qty = position.qty()

        position._qty -= qty
        soldValue = qty * stock.bar.close
        self.totalCash += soldValue

        if position.qty() == 0:
            stock.position = None
            position.stopPrice = None

        position.stats.addSell(self.curDate, soldValue, stock.bar.close)

        o = BacktestOrder(OrderType.SELL, stock.symbol, qty, stock.bar.close, self.curDate)

        self._next_n.addTrade(symbol=stock.symbol, side="Sell", qty=qty, price=stock.bar.close, value=soldValue)

        stock.unsettledFunds[-1] += soldValue

        self.notifyOrderEvent(o)

    def submitUpdateStop(self, stock: Stock, stopPrice: float) -> None:
        checkStop(stopPrice)
        if not isinstance(stock.position, BackTestPosition):
            return

        stock.position.stopPrice = stopPrice

    def getRunStats(self) -> RunStats:
        symbolStats: Dict[str, _TradeList] = {}
        totalStats = _TradeList()

        for sym, position in self.positions.items():
            symbolStats[sym] = position.stats

            totalStats.winList.extend(position.stats.winList)
            totalStats.lossList.extend(position.stats.lossList)
        # end for symbol

        return RunStats(self.startingVal, self.totalCash, totalStats, symbolStats)
