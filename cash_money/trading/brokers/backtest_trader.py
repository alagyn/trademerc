from typing import Union, Tuple, Dict, List, Optional, Any
import numpy as np
import math
import datetime
import logging

from cash_money import cmErrors
from cash_money.trading.objects import Bar, Order, OrderType, OrderStatus, Stock, CMPosition, StockStatus
from cash_money.trading.trader import Trader
from cash_money.trading.notifiers.console_notifier import ConsoleNotifier
from cash_money.trading.notifiers.notifier import Notification
from cash_money.utils.run_utils import BarDict
from cash_money.utils.date_utils import nextBusinessDay
from cash_money.trading.nodeStrategy import NodeStrategy

log = logging.getLogger("Backtest Brkr")
statLog = logging.getLogger("Stats")


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

        self.stats = Stats()

    def getstatus(self) -> StockStatus:
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

    def __init__(self):
        super().__init__(BacktestOrderStub._ID_GEN)
        BacktestOrderStub._ID_GEN += 1


class BacktestOrder(BacktestOrderStub):

    def __init__(
        self,
        orderT: OrderType,
        symbol: str,
        qty: int,
        price: float,
        stopLimit: Optional[float] = None
    ):
        super().__init__()
        self.stat = OrderStatus.UNFILLED
        self.price = price
        self._sym = symbol
        self._qty = qty
        self._orderType = orderT
        self._sl = stopLimit

    def status(self) -> OrderStatus:
        return self.stat

    def orderType(self) -> OrderType:
        raise NotImplemented

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
        if self._sl is not None:
            return self._sl
        else:
            return None

    def data(self) -> Any:
        return None


def checkStop(stop: float):
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

    return float(a * b / c)


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

        self.notif = ConsoleNotifier()
        self._next_n = Notification()

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
                    position.stats.addSell(
                        self.curDate, newCash, position.stopPrice
                    )
                    # Reset position
                    position._qty = 0
                    position.stopPrice = None

                    log.info(f"{sym}: Stop Activated, Value: ${newCash:.2f}")

        return True

    def postTrade(self) -> None:
        if self.totalCash < 0:
            raise cmErrors.BacktestError(
                'BacktestBroker.postTrade() Negative Buy Power, Strategy Failure?'
            )

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

        self.notif.update(self._next_n)
        self._next_n = Notification()

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
                log.info(
                    f"    [{sym}] Qty: {position.qty()}, Value: ${newCash:.2f}"
                )

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

    def submitBuy(
        self,
        stock: Stock,
        qty: int,
        stopLimit: Optional[float] = None
    ) -> None:
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
            stock.stopOrder = BacktestOrderStub()
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

        o = BacktestOrder(t, stock.symbol, qty, stock.bar.close, stopLimit)
        stock.order = o
        stock.buyDate = self.curDate

        self._next_n.addTrade(
            symbol=stock.symbol,
            side="Buy",
            qty=qty,
            price=stock.bar.close,
            value=stock.bar.close * qty
        )

    def closePosition(self, stock: Stock) -> None:
        if stock.position is not None:
            self.submitSell(stock, stock.position.qty())
        else:
            log.warn(
                f"Cannot close position for {stock.symbol}, no position open"
            )

    def closeAllPositions(self) -> None:
        for stock in self.stocks.values():
            if stock.position is not None and stock.position.qty() > 0:
                self.closePosition(stock)

    def submitSell(self, stock: Stock, qty: int) -> None:
        if stock.bar is None:
            log.warn(f"Cannot submit sell for {stock.symbol}, bar is None")
            raise RuntimeError()
            return

        if stock.position is None:
            log.warn(
                f"Cannot submit sell for {stock.symbol}, no position open"
            )
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

        self._next_n.addTrade(
            symbol=stock.symbol,
            side="Sell",
            qty=qty,
            price=stock.bar.close,
            value=soldValue
        )

        stock.unsettledFunds[-1] += soldValue

    def submitUpdateStop(self, stock: Stock, stopPrice: float) -> None:
        checkStop(stopPrice)
        stock.position.stopPrice = stopLimit[0]  # type: ignore

    def getRunStats(self, logToConsole: bool) -> Dict[str, Any]:
        wins = 0
        losses = 0
        winTotal = 0
        lossTotal = 0

        tradeList = []

        for sym, position in self.positions.items():
            stat = position.stats
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

        if logToConsole:
            statLog.info(
                f'Start Value: ${self.startingVal:,.2f}, End Value: ${self.totalCash:,.2f}'
            )
            statLog.info(
                f'Profit: {profit:,.2f}, Percent Gain: {percentGain:.2%}'
            )
            statLog.info(
                f'Trades: {numTrades}, Wins: {wins}, Losses: {losses}, W/L: {wlRatio:.2f}'
            )
            statLog.info(f'Win %: {winPercent:.2%}')
            statLog.info(f'Avg Gain: ${avgGain:,.2f}')
            statLog.info(f'Avg Loss: ${avgLoss:,.2f}')
            statLog.info(f'SQN: {sqnVal:.3f}')

        return {
            'StartValue': f"{self.startingVal:,.2f}",
            'EndValue': f"{self.totalCash:,.2f}",
            'Profit': f"{profit:,.2f}",
            'PercentGain': f"{percentGain:.2%}",
            'SQN': f"{sqnVal:.3f}",
            'trades': str(numTrades),
            'wins': str(wins),
            'losses': str(losses),
            'wl': f"{wlRatio:.2f}",
            'winPerc': f"{winPercent:.2%}",
            'avgGain': f"{avgGain:,.2f}",
            'avgLoss': f"{avgLoss:,.2f}"
        }
