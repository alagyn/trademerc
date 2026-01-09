from typing import List, Dict, Optional, Tuple, Any
import threading
import logging
from collections import defaultdict
import datetime
import time
import sys
import traceback

import imgui as im
from imgui import implot

from ..ui_state import UIState
from ..fileSelect import askOpenFile

from cash_money.trading.events import ActionEvent, CMEventListener, EndOfTradeStepEvent, LineUpdateEvent, OrderEvent, StockUpdateEvent
from cash_money.trading.nodeStrategy import loadStratFromJson
from cash_money import backtester
from cash_money.trading.brokers.backtest_trader import RunStats
from cash_money.trading.objects import Action, ActionEnum, OrderType, OrderStatus
from cash_money.trading.data.dataBroker import DataBroker

log = logging.getLogger("BT GUI")

BUY_COL = im.Vec4(0, 1, 0, 1)
SELL_COL = im.Vec4(1, 0, 0, 1)

STATS_WIDTH = 200

SPIN_STATES = ["\\", "|", "/", "-"]

PLOT_HEIGHT = 250
PLOT_WIDTH_PERC = 0.7


def clip(minVal, val, maxVal):
    if val.val < minVal:
        val.val = minVal
    elif maxVal < val.val:
        val.val = maxVal


def parseDate(dateStr: im.StrRef) -> datetime.datetime:
    return datetime.datetime.strptime(dateStr.copy(), "%m/%d/%Y")


def printDate(date: datetime.datetime) -> str:
    return date.strftime("%m/%d/%Y")


START_DATE_CACHE = "bt_start"
END_DATE_CACHE = "bt_end"
CASH_CACHE = "bt_cash"


class BacktesterTab(CMEventListener):

    def __init__(self, cache: Dict[str, Any], dataBroker: DataBroker) -> None:

        self.dataBroker = dataBroker
        self.buys: Dict[str, Tuple[im.DoubleList,
                                   im.DoubleList]] = defaultdict(lambda: (im.DoubleList(), im.DoubleList()))
        self.sells: Dict[str, Tuple[im.DoubleList,
                                    im.DoubleList]] = defaultdict(lambda: (im.DoubleList(), im.DoubleList()))

        self.pos_values: Dict[str, im.DoubleList] = defaultdict(im.DoubleList)
        self.portfolio = im.DoubleList()
        self.portfolio_ts = im.DoubleList()
        self.stock_closes: Dict[str, im.DoubleList] = defaultdict(im.DoubleList)
        self.data_lock = threading.Semaphore()
        self.reset_axes = False

        self.runThread: Optional[threading.Thread] = None

        self.selectedStockIdx = im.IntRef(0)

        self.runStats: Optional[RunStats] = None

        self.spinIdx = 0
        self.spinTime = time.time()

        self.stocks: List[str] = []

        self.startDateStr = im.StrRef(
            str(datetime.datetime.now().replace(year=datetime.datetime.now().year - 1).strftime("%m/%d/%Y")), 20
        )
        self.validStartDateStr = True

        self.endDateStr = im.StrRef(str(datetime.datetime.now().strftime("%m/%d/%Y")), 20)
        self.validEndDateStr = True

        self.startDate = parseDate(self.startDateStr)
        self.endDate = parseDate(self.endDateStr)

        try:
            self.startingCash = im.IntRef(cache[CASH_CACHE])
        except KeyError:
            self.startingCash = im.IntRef(10000)

        self.errorMessage = ""

        # linked plot dimensions
        self.plotRectXMin = im.DoubleRef()
        self.plotRectXMax = im.DoubleRef()

        self.lines: dict[str, dict[str, im.DoubleList]] = defaultdict(lambda: defaultdict(im.DoubleList))

    def cleanup(self, cache: Dict[str, Any]):
        cache[START_DATE_CACHE] = printDate(self.startDate)
        cache[END_DATE_CACHE] = printDate(self.endDate)
        cache[CASH_CACHE] = self.startingCash.val

    def render(self, state: UIState) -> None:
        if self.selectedStockIdx.val > len(state.stocks):
            self.selectedStockIdx.val = 0

        if im.BeginTable("config table", 2):
            im.TableNextColumn()
            if im.Button(" Load Strategy "):
                state.askStrat()
            im.SameLine()
            im.Text(state.stratFile)

            if im.Button("Load Stock List"):
                state.askStocks()
            im.SameLine()
            im.Text(state.stockFile)

            im.TableNextColumn()

            im.SetNextItemWidth(100)
            if im.InputTextWithHint("Start Date", "mm/dd/yyyy", self.startDateStr):
                try:
                    self.startDate = parseDate(self.startDateStr)
                    self.validStartDateStr = True
                except ValueError:
                    self.validStartDateStr = False

            if not self.validStartDateStr:
                im.SameLine()
                im.Dummy(im.Vec2(10, 0))
                im.SameLine()
                im.Text("Invalid Date")

            im.SetNextItemWidth(100)
            if im.InputTextWithHint("End Date", "mm/dd/yyyy", self.endDateStr):
                try:
                    self.endDate = parseDate(self.endDateStr)
                    self.validEndDateStr = True
                except ValueError:
                    self.validEndDateStr = False

            if not self.validEndDateStr:
                im.SameLine()
                im.Dummy(im.Vec2(10, 0))
                im.SameLine()
                im.Text("Invalid Date")

            im.SetNextItemWidth(100)
            im.InputInt("Starting Cash ($)", self.startingCash, step=100, step_fast=1000)

            im.EndTable()

        im.BeginDisabled(self.runThread is not None or len(state.stratFile) == 0 or len(state.stocks) == 0)
        if im.Button("Run Backtest"):
            self.errorMessage = ""
            self.resetPlots()
            self.stocks = state.stocks.copy()

            try:
                strats = {
                    x: loadStratFromJson(state.stratGraph.getJSON(), x)
                    for x in state.stocks
                }

                self.runThread = threading.Thread(
                    target=self._run_backtest_thread,
                    args=(
                        strats,
                        self.startDate,
                        self.endDate,
                        self.dataBroker,
                        self.startingCash.val,
                        "stats.json",  # TODO
                        self
                    )
                )
                self.runThread.start()
            except Exception as err:
                log.error("Error running backtest: %s", "".join(traceback.format_exception(err)))
                self.errorMessage = f"Backtesting failed, Error: {err}"
                pass

        im.EndDisabled()

        if self.runThread is not None:
            curTime = time.time()
            if curTime - self.spinTime > 1:
                self.spinTime = curTime
                self.spinIdx = (self.spinIdx + 1) % len(SPIN_STATES)
            im.SameLine()
            im.Text(f'Running... {SPIN_STATES[self.spinIdx]}')
        elif len(self.errorMessage) > 0:
            im.SameLine()
            im.Text(self.errorMessage)

        if self.runThread is not None and not self.runThread.is_alive():
            self.runThread.join()
            self.runThread = None

        im.Separator()

        # Calculate available width for plots and stats
        available_width = im.GetContentRegionAvail().x
        plot_width = available_width * PLOT_WIDTH_PERC
        plot_dim = im.Vec2(plot_width, PLOT_HEIGHT)

        tableFlags = im.TableFlags.SizingFixedFit

        if implot.BeginAlignedPlots("backtest_graphs"):
            # Portfolio plot with summary at the top
            if im.BeginTable("Portfolio Row", 2, tableFlags):
                im.TableNextColumn()

                # Portfolio plot
                with self.data_lock:
                    if self.reset_axes:
                        implot.SetNextAxesToFit()
                    if len(self.portfolio) > 0 and implot.BeginPlot("Portfolio Value##plot", plot_dim):
                        implot.SetupAxisLinks(implot.Axis.X1, self.plotRectXMin, self.plotRectXMax)

                        implot.SetupAxisScale(implot.Axis.X1, implot.Scale.Time)
                        implot.SetupAxisFormat(implot.Axis.Y1, "$%g")

                        # Plot position values for each symbol
                        for symbol, arr in self.pos_values.items():
                            if len(arr) > 0:
                                implot.PlotLine(f"{symbol}##pos", self.portfolio_ts, arr)

                        # Plot overall portfolio value
                        if len(self.portfolio) > 0:
                            implot.PlotLine("Portfolio Value##total", self.portfolio_ts, self.portfolio)

                        implot.EndPlot()

                # Portfolio stats (keep the same)
                im.TableNextColumn()
                if self.runStats:
                    im.Text(f"Portfolio Summary")
                    im.Separator()
                    im.Text(f"Starting Value: ${self.runStats.startValue:,.2f}")
                    im.Text(f"Ending Value: ${self.runStats.endValue:,.2f}")
                    total_profit = sum(stats.profit for stats in self.runStats.symbolStats.values())
                    im.Text(f"Total Profit: ${total_profit:,.2f}")
                    im.Text(
                        f"Total % Gain: {(self.runStats.endValue - self.runStats.startValue) / self.runStats.startValue:.2%}"
                    )
                    im.Text(f"SQN: {self.runStats.totalStats.sqn:.3f}")
                else:
                    im.Text("No portfolio data available")

                im.EndTable()

            im.Separator()
            # Individual stock plots with their stats
            if im.BeginChild("Stocks"):  # child window to keep the portfolio from scrolling away
                for symbol in self.stocks:
                    if im.BeginTable(f"Stock Row {symbol}", 2, tableFlags):
                        im.TableNextColumn()

                        # Stock plot
                        with self.data_lock:
                            if self.reset_axes:
                                implot.SetNextAxesToFit()
                            if len(self.stock_closes[symbol]) > 0 and implot.BeginPlot(f"{symbol}##plot", plot_dim):

                                implot.SetupAxisLinks(implot.Axis.X1, self.plotRectXMin, self.plotRectXMax)

                                implot.SetupAxisScale(implot.Axis.X1, implot.Scale.Time)
                                implot.SetupAxisFormat(implot.Axis.Y1, "$%g")

                                buys, buys_ts = self.buys[symbol]
                                sells, sells_ts = self.sells[symbol]

                                # Plot price line
                                closes = self.stock_closes[symbol]
                                if len(closes) > 0:
                                    implot.PlotLine(f"Price##{symbol}", self.portfolio_ts, closes)

                                # Plot buy/sell markers
                                if len(buys) > 0:
                                    implot.PushStyleColor(implot.Col.MarkerOutline, BUY_COL)
                                    implot.PlotScatter(f"Buy##{symbol}", buys_ts, buys)
                                    implot.PopStyleColor()

                                if len(sells) > 0:
                                    implot.PushStyleColor(implot.Col.MarkerOutline, SELL_COL)
                                    implot.PlotScatter(f"Sell##{symbol}", sells_ts, sells)
                                    implot.PopStyleColor()

                                for key, line in self.lines[symbol].items():
                                    if (len(self.portfolio_ts) == len(line)):
                                        implot.PlotLine(key, self.portfolio_ts, line)

                                implot.EndPlot()

                            # Stock stats (keep the same)
                            im.TableNextColumn()
                            if self.runStats and symbol in self.runStats.symbolStats:
                                stats = self.runStats.symbolStats[symbol]
                                weight = abs(stats.profit) / self.runStats.endValue

                                im.Text(f"{symbol} Summary")
                                im.Separator()
                                im.Text(f"Weight: {weight:.2%}")
                                im.Text(f"Profit: ${stats.profit:,.2f}")
                                im.Text(f"% Gain: {stats.percGain:.2%}")
                                im.Text(f"SQN: {stats.sqn:.3f}")
                                im.Text(f"Trades: {stats.trades}")
                                im.Text(f"Win/Loss: {stats.wins}/{stats.losses}")
                                im.Text(f"Win %: {stats.winPerc:.2%}")
                                im.Text(f"Avg Gain: ${stats.avgGain:,.2f}")
                                im.Text(f"Avg Loss: ${stats.avgLoss:,.2f}")
                            else:
                                im.Text(f"No data available for {symbol}")

                            im.EndTable()

                    im.Separator()
            im.EndChild()
            implot.EndAlignedPlots()

        # Reset the axes flag after rendering all plots
        self.reset_axes = False

    def resetPlots(self):
        with self.data_lock:
            self.portfolio.clear()
            self.portfolio_ts.clear()
            self.buys.clear()
            self.sells.clear()
            self.pos_values.clear()
            self.stock_closes.clear()
            self.lines.clear()

    # Thread handler for backtesting
    # passes args to backetest func
    def _run_backtest_thread(self, *args, **kwargs):
        try:
            self.runStats = backtester.backtest(*args, **kwargs)
        except Exception as err:
            log.error("Error running backtest: %s", "".join(traceback.format_exception(err)))
            self.errorMessage = f'Backtest error: {str(err)}'

    # Event listener funcs

    def onOrder(self, event: OrderEvent):
        with self.data_lock:
            order = event.order
            value = order.filledAvgPrice()
            orderTS = order.timestamp().timestamp()
            if order.orderType() == OrderType.BUY:
                data, ts = self.buys[order.symbol()]
            if order.orderType() == OrderType.SELL:
                data, ts = self.sells[order.symbol()]

            data.append(value)
            ts.append(orderTS)

    def onStockUpdate(self, event: StockUpdateEvent):
        #log.warn("Update %s %f", event.symbol, event.bar.close)
        with self.data_lock:
            self.reset_axes = True
            #self.stock_closes[event.symbol].append(event.bar.close)
            #self.stock_closes_ts[event.symbol].append(event.bar.date.timestamp())

    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        # log.warn("End of trade step")
        with self.data_lock:
            self.portfolio.append(event.notif.equity_cur)
            ts = event.notif.date.timestamp()
            self.portfolio_ts.append(ts)
            seen = set()
            for x in event.notif.positions:
                self.pos_values[x.symbol].append(x.value)
                seen.add(x.symbol)

            for sym in self.stocks:
                if sym not in seen:
                    self.pos_values[sym].append(0)

            for sym, bar in event.notif.bars.items():
                self.stock_closes[sym].append(bar.close)

    def onLineUpdate(self, event: LineUpdateEvent):
        with self.data_lock:
            self.lines[event.symbol][event.key].append(event.value)
