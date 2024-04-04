from typing import List, Dict
from collections import defaultdict
import logging
from threading import Semaphore

from cash_money.trading.events import ActionEvent, CMEventListener, EndOfTradeStepEvent, StockUpdateEvent

import imgui as im
import imgui.implot as implot
import numpy as np


def _array():
    return np.array(list(), dtype=np.float64, order='C')  # type: ignore


log = logging.getLogger("GUI")


class ListenerGUI(CMEventListener):

    def __init__(self) -> None:
        self.actions: List[ActionEvent] = []
        self.stock_closes: Dict[str, np.ndarray] = defaultdict(_array)
        self.stock_closes_ts: Dict[str, np.ndarray] = defaultdict(_array)
        self.portfolio = _array()
        self.portfolio_ts = _array()
        self.data_lock = Semaphore()
        self.reset_axes = False

    def render(self):
        with self.data_lock:
            im.Begin("Actions")
            if self.reset_axes:
                implot.SetNextAxesToFit()
            implot.BeginPlot("Closes")
            implot.SetupAxisScale(implot.Axis.X1, implot.Scale.Time)
            implot.SetupAxisScale(implot.Axis.Y1, implot.Scale.Log10)
            for symbol, arr in self.stock_closes.items():
                implot.PlotLine(symbol, self.stock_closes_ts[symbol], arr)
            implot.PlotLine("Portfolio", self.portfolio_ts, self.portfolio)
            implot.EndPlot()
            im.End()

    def onAction(self, event: ActionEvent):
        self.actions.append(event)

    def onStockUpdate(self, event: StockUpdateEvent):
        #log.warn("Update %s %f", event.symbol, event.bar.close)
        with self.data_lock:
            self.reset_axes = True
            arr = self.stock_closes[event.symbol]
            # this makes copies... ugh
            # TODO change these to be list wrappers...
            self.stock_closes[event.symbol] = np.append(arr, [event.bar.close])
            arr = self.stock_closes_ts[event.symbol]
            self.stock_closes_ts[
                event.symbol] = np.append(arr, [event.bar.date.timestamp()])
            
    def onEndOfTradeStep(self, event: EndOfTradeStepEvent):
        log.warn("End of trade step")
        with self.data_lock:
            self.portfolio = np.append(self.portfolio, [event.notif.equity_cur])
            self.portfolio_ts = np.append(self.portfolio_ts, [event.notif.date.timestamp()])


if __name__ == '__main__':
    from cash_money.gui.cm_window import run_window
    from threading import Thread
    import time

    def main():
        gui = ListenerGUI()

        args = (800, 600, "Test", gui.render)

        #run_window(*args)

        thread = Thread(target=run_window, args=args, daemon=True)
        thread.start()
        while thread.is_alive():
            time.sleep(0.5)

    main()
