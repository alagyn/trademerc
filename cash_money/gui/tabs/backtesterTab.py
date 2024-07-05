from typing import List, Dict, Optional, Tuple, Any
import threading
import logging
from collections import defaultdict
import datetime
import time
import sys

import imgui as im
from imgui import implot

from ..ui_state import UIState
from ..fileSelect import askOpenFile

from cash_money.trading.events import ActionEvent, CMEventListener, EndOfTradeStepEvent, OrderEvent, StockUpdateEvent
from cash_money.trading.nodeStrategy import NodeStrategy
from cash_money import backtester
from cash_money.trading.brokers.backtest_trader import BacktestStats
from cash_money.trading.objects import Action, ActionEnum, OrderType, OrderStatus

log = logging.getLogger("BT GUI")

BUY_COL = im.Vec4(0, 1, 0, 1)
SELL_COL = im.Vec4(1, 0, 0, 1)

STATS_WIDTH = 200

SPIN_STATES = ["\\", "|", "/", "-"]


def clip(minVal, val, maxVal):
    if val.val < minVal:
        val.val = minVal
    elif maxVal < val.val:
        val.val = maxVal


def parseDate(dateStr: im.StrRef) -> datetime.datetime:
    return datetime.datetime.strptime(dateStr.copy(), "%m/%d/%Y")


class BacktesterTab(CMEventListener):

    def __init__(self) -> None:

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

        self.runStats = BacktestStats()

        self.spinIdx = 0
        self.spinTime = time.time()

        self.stocks: List[str] = []

        self.startDateStr = im.StrRef("1/1/2020", 20)
        self.validStartDateStr = True

        self.endDateStr = im.StrRef("1/1/2021", 20)
        self.validEndDateStr = True

        self.startDate = datetime.datetime(2020, 1, 1)
        self.endDate = datetime.datetime(2021, 1, 1)

        self.startingCash = im.IntRef(10000)

    def render(self, state: UIState) -> None:
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

            self.resetPlots()
            self.stocks = state.stocks.copy()

            try:
                strats = {
                    x: NodeStrategy(state.stratData['graph'], x)
                    for x in state.stocks
                }

                self.runThread = threading.Thread(
                    target=backtester.backtest,
                    args=(
                        state.stratData['name'],
                        strats,
                        None,  # TODO remove
                        None,  # TODO remove
                        self.startDate,
                        self.endDate,
                        self.startingCash.val,
                        self.runStats,
                        "stats.json",  # TODO
                        self
                    )
                )
                self.runThread.start()
            except:
                # TODO
                pass

        im.EndDisabled()

        if self.runThread is not None:
            curTime = time.time()
            if curTime - self.spinTime > 1:
                self.spinTime = curTime
                self.spinIdx = (self.spinIdx + 1) % len(SPIN_STATES)
            im.SameLine()
            im.Text(f'Running... {SPIN_STATES[self.spinIdx]}')

        if self.runThread is not None and not self.runThread.is_alive():
            self.runThread.join()
            self.runThread = None

        im.Separator()

        im.BeginDisabled()
        im.Text("Selected Stock:")
        im.NewLine()
        im.EndDisabled()
        for idx, x in enumerate(state.stocks):
            im.SameLine()
            if im.RadioButton(x, self.selectedStockIdx, idx):
                self.reset_axes = True

        if im.BeginTable("mainTable", 2, flags=im.TableFlags.SizingFixedFit):
            im.TableNextColumn()
            im.TableSetupColumn("stats", 0, STATS_WIDTH)

            self.renderStats()
            im.TableNextColumn()
            name = state.stocks[self.selectedStockIdx.val] if len(state.stocks) > 0 else "  "
            self.renderPlots(name)
            im.EndTable()

    def resetPlots(self):
        with self.data_lock:
            self.portfolio.clear()
            self.portfolio_ts.clear()
            self.buys.clear()
            self.sells.clear()
            self.pos_values.clear()
            self.stock_closes.clear()

    def renderPlots(self, selectedStock: str):
        with self.data_lock:
            vp = im.GetMainViewport()

            if implot.BeginSubplots("Run Data",
                                    2,
                                    1,
                                    im.Vec2(im.GetWindowWidth() - im.GetCursorPosX(), 500),
                                    flags=implot.SubplotFlags.LinkAllX):
                if self.reset_axes:
                    implot.SetNextAxesToFit()

                if implot.BeginPlot("Value"):
                    implot.SetupAxisScale(implot.Axis.X1, implot.Scale.Time)
                    implot.SetupAxisLimits(implot.Axis.Y1, 0, 10000)  # TODO
                    implot.SetupAxisFormat(implot.Axis.Y1, "$%g")
                    #implot.SetupAxisScale(implot.Axis.Y1, implot.Scale.Log10)
                    for symbol, arr in self.pos_values.items():
                        implot.PlotLine(symbol, self.portfolio_ts, arr)
                    implot.PlotLine("Portfolio Cash", self.portfolio_ts, self.portfolio)
                    implot.EndPlot()
                # Selected stock data

                if self.reset_axes:
                    implot.SetNextAxisToFit(implot.Axis.Y1)

                if implot.BeginPlot(f"Selected Stock: {selectedStock}###selected_stock"):
                    implot.SetupAxisScale(implot.Axis.X1, implot.Scale.Time)
                    implot.SetupAxisFormat(implot.Axis.Y1, "$%g")
                    #value = self.pos_values[selectedStock]
                    #implot.PlotLine(selectedStock, self.portfolio_ts, value)

                    buys, buys_ts = self.buys[selectedStock]
                    sells, sells_ts = self.sells[selectedStock]

                    implot.PushStyleColor(implot.Col.MarkerOutline, BUY_COL)
                    implot.PlotScatter("Buy Value", buys_ts, buys)
                    implot.PushStyleColor(implot.Col.MarkerOutline, SELL_COL)
                    implot.PlotScatter("Sell Value", sells_ts, sells)
                    implot.PopStyleColor(2)

                    closes = self.stock_closes[selectedStock]
                    implot.PlotLine("Price", self.portfolio_ts, closes)

                    implot.EndPlot()

                self.reset_axes = False
                implot.SetupLegend(implot.Location.South)
                implot.EndSubplots()
        # end beginsubplots

    def renderStats(self):
        if im.BeginTable("stats", 2, outer_size=im.Vec2(STATS_WIDTH, 0)):

            def item(label, data):
                im.TableNextColumn()
                im.Text(label)
                im.TableNextColumn()
                im.Text(data)

            item("Starting Value", f'${self.runStats.startValue:,.2f}')
            item("Ending Value", f'${self.runStats.endValue:,.2f}')
            item("Profit", f'${self.runStats.profit:,.2f}')
            item("Percent Gain", f'{self.runStats.percGain:.2%}')
            item("SQN", f'{self.runStats.SQN:.3f}')
            item("Trades", str(self.runStats.trades))
            item("Wins", str(self.runStats.wins))
            item("Losses", str(self.runStats.losses))
            item("W/L ratio", f'{self.runStats.wlRatio:.2%}')
            item("Avg. Gain", f'${self.runStats.avgGain:,.2f}')
            item("Avg. Loss", f'${self.runStats.avgLoss:,.2f}')

            im.EndTable()

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
            self.portfolio.append(event.notif.cash)
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
