import datetime
import json
import os.path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict

from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from tkcalendar import DateEntry

import cm_backtester
from cmErrors import StrategyError
from run_alpaca import runTrader
from strategies.customStrategy import makeCustomStrategy
from utils.file_utils import loadStockFile

STRAT_FT = [('Strategy', '.strat')]

class BTGUI(tk.Frame):
    def __init__(self, root):
        self.root = root
        super().__init__(self.root)

        self.root.protocol("WM_DELETE_WINDOW", self.closeWindow)

        self.stocks = []
        self.stratFile = ''

        # ROOT
        self.root.title("Backtester")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.grid(column=0, row=0, sticky='nesw')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)

        self.rowconfigure(0, weight=1)

        # MENU
        self.root.option_add('*tearOff', tk.FALSE)
        menubar = tk.Menu(self.root)
        self.root['menu'] = menubar

        # Run frame
        #region
        runFrame = tk.LabelFrame(self, text="Run")

        LOAD_BTN_ROW = 0

        loadStratBtn = tk.Button(runFrame, text='Load Strategy', command=self.selectStrat)
        loadStratBtn.grid(row=LOAD_BTN_ROW, column=0, columnspan=2, sticky='ew', padx=5, pady=2)

        CUR_STRAT_ROW = LOAD_BTN_ROW + 1

        tk.Label(runFrame, text='Current Strategy:').grid(row=CUR_STRAT_ROW, column=0)
        self.stratNameVar = tk.StringVar()
        tk.Label(runFrame, textvariable=self.stratNameVar).grid(row=CUR_STRAT_ROW, column=1)

        SEP0_ROW = CUR_STRAT_ROW + 1

        ttk.Separator(runFrame, orient=tk.HORIZONTAL).grid(row=SEP0_ROW, column=0,
                                                           columnspan=2, sticky='ew',
                                                           pady=10)

        START_VAL_ROW = SEP0_ROW + 1

        tk.Label(runFrame, text='Starting Value ($):').grid(row=START_VAL_ROW, column=0, sticky='ew')
        self.startValVar = tk.IntVar(value=10000)
        tk.Spinbox(runFrame, textvariable=self.startValVar).grid(row=START_VAL_ROW, column=1, sticky='ew')

        SYMBOL_BTN_ROW = START_VAL_ROW + 1

        symbolBtn = tk.Button(runFrame, text='Load Symbols', command=self.selectSymbolFile)
        symbolBtn.grid(row=SYMBOL_BTN_ROW, column=0, columnspan=2, sticky='ew', padx=5, pady=2)

        SYMBOL_IN_ROW = SYMBOL_BTN_ROW + 1

        tk.Label(runFrame, text='Symbols:').grid(row=SYMBOL_IN_ROW, column=0, padx=2)
        self.symbolVar = tk.StringVar()
        symbolLabel = tk.Label(runFrame, textvariable=self.symbolVar)
        symbolLabel.grid(row=SYMBOL_IN_ROW, column=1, padx=2)

        SEP1_ROW = SYMBOL_IN_ROW + 1

        ttk.Separator(runFrame, orient=tk.HORIZONTAL).grid(row=SEP1_ROW, column=0,
                                                           columnspan=2, sticky='ew',
                                                           pady=10)

        START_DATE_ROW = SEP1_ROW + 1

        startLabel = tk.Label(runFrame, text='Start Date:')
        startLabel.grid(row=START_DATE_ROW, column=0, sticky='ew')

        md = datetime.datetime.today() - datetime.timedelta(1)

        self.startInput = DateEntry(runFrame, maxdate=md)
        self.startInput.grid(row=START_DATE_ROW, column=1, sticky='ew', padx=5)
        self.startInput.set_date(datetime.datetime(2018, 1, 1))

        END_DATE_ROW = START_DATE_ROW + 1

        endLabel = tk.Label(runFrame, text='End Date:')
        endLabel.grid(row=END_DATE_ROW, column=0, sticky='ew')

        self.endInput = DateEntry(runFrame, maxdate=md)
        self.endInput.grid(row=END_DATE_ROW, column=1, sticky='ew', padx=5)
        self.endInput.set_date(md)

        SEP2_ROW = END_DATE_ROW + 1
        ttk.Separator(runFrame, orient=tk.HORIZONTAL).grid(row=SEP2_ROW, column=0,
                                                           columnspan=2, sticky='ew',
                                                           pady=10)

        OUT_BTN_ROW = SEP2_ROW + 1

        outbtn = tk.Button(runFrame, text='Select Output:', command=self.selectOut)
        outbtn.grid(row=OUT_BTN_ROW, column=0, padx=2)
        self.outVar = tk.StringVar()
        self.outVar.set('stats.json')
        outLabel = tk.Label(runFrame, textvariable=self.outVar)
        outLabel.grid(row=OUT_BTN_ROW, column=1, padx=2)

        INDIV_TOGGLE_ROW = OUT_BTN_ROW + 1

        self.indivVar = tk.BooleanVar()
        tk.Checkbutton(runFrame, text='Individual Runs?', variable=self.indivVar).grid(row=INDIV_TOGGLE_ROW, column=0,
                                                                                       columnspan=2)

        RUN_BTN_ROW = INDIV_TOGGLE_ROW + 1

        runBtn = tk.Button(runFrame, text='Run Backtest', command=self.runBT)
        runBtn.grid(row=RUN_BTN_ROW, column=0, columnspan=2, sticky='ew', padx=5)

        LIVE_TOGGLE_ROW = RUN_BTN_ROW + 2
        self.liveToggleVar = tk.BooleanVar(value=False)
        liveCheckBox = tk.Checkbutton(runFrame, text='LIVE Account?', variable=self.liveToggleVar)
        liveCheckBox.grid(row=LIVE_TOGGLE_ROW, column=0, columnspan=2)

        RUN_LIVE_BTN_ROW = LIVE_TOGGLE_ROW + 1

        liveBtn = tk.Button(runFrame, text='Run on Alpaca', command=self.runAlpaca)
        liveBtn.grid(row=RUN_LIVE_BTN_ROW, column=0, columnspan=2, sticky='ew', padx=5)
        #endregion

        # GRID MAIN FRAMES
        FRAME_PAD = 5

        # STAT FRAME
        statFrame = tk.LabelFrame(self, text='Stats')

        row = 0

        self.statVars: Dict[str, tk.Variable] = {}

        for k, v in cm_backtester.STATS:
            var = tk.DoubleVar(value=0)
            self.statVars[k] = var

            tk.Label(statFrame, text=v, anchor='e').grid(row=row, column=0, sticky='new')
            tk.Label(statFrame, textvariable=var).grid(row=row, column=1, sticky='new')

            row += 1


        # GRAPH FRAME
        mainGraphFrame = tk.Frame(self)
        mainGraphFrame.columnconfigure(0, weight=1)
        mainGraphFrame.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(mainGraphFrame)
        self.notebook.grid(row=0, column=0, sticky='nesw')

        self.masterFigure = None
        self.nbFrames = []
        self.figures = {}
        self.canvases = []

        runFrame.grid(row=0, column=0, sticky='nsew', padx=FRAME_PAD)
        statFrame.grid(row=0, column=1, sticky='nesw', padx=FRAME_PAD)
        mainGraphFrame.grid(row=0, column=2, sticky='news', padx=FRAME_PAD)
        # stratFrame.grid(row=0, column=1, sticky='nsew', padx=FRAME_PAD)

    def closeWindow(self):
        self.root.destroy()

    def selectOut(self):
        # noinspection PyArgumentList
        ret = filedialog.askopenfilename(filetypes=[('json', 'json')], multiple=False, initialdir='.')
        if len(ret) > 0:
            self.outVar.set(ret)

    def selectStrat(self):
        # noinspection PyArgumentList
        ret = filedialog.askopenfilename(filetypes=STRAT_FT, multiple=False, initialdir='./config')
        if len(ret) > 0:
            try:
                self.stratFile = ret
                _, name = os.path.split(ret)
                self.stratNameVar.set(name)
            except StrategyError as err:
                messagebox.showerror("Strategy Error", str(err))

    def selectSymbolFile(self):
        # noinspection PyArgumentList
        ret = filedialog.askopenfilename(filetypes=[('.txt', '.txt')], multiple=False, initialdir='./config')
        if len(ret) > 0:
            self.stocks = loadStockFile(ret)
            _, f = os.path.split(ret)
            self.symbolVar.set(f)

            self.genGraphs()

    def createPlotCanvas(self, text) -> Figure:
        frame = ttk.Frame(self.notebook)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=2)
        frame.rowconfigure(1, weight=1)

        self.notebook.add(frame, text=text, sticky='nesw')
        self.nbFrames.append(frame)
        fig = Figure()
        canvas = FigureCanvasTkAgg(fig, master=frame)

        self.canvases.append(canvas)

        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, frame, pack_toolbar=False)
        toolbar.update()

        canvas.mpl_connect(
            "key_press_event", key_press_handler
        )

        canvas.get_tk_widget().grid(row=0, column=0, sticky='nesw')
        toolbar.grid(row=1, column=0, sticky='ews')

        return fig

    def genGraphs(self):
        for x in self.notebook.tabs():
            self.notebook.forget(x)

        self.nbFrames = []
        self.figures = {}
        self.canvases = []

        self.masterFigure = self.createPlotCanvas("Portfolio")

        for sym in self.stocks:
            self.figures[sym] = self.createPlotCanvas(sym)


    def runBT(self):
        if len(self.stocks) <= 0 or len(self.stratFile) == 0:
            return

        with open(self.stratFile, mode='r') as f:
            strat = json.load(f)

        startDate = self.startInput.get_date()
        endDate = self.endInput.get_date()

        args = {
            "stratName": strat['name'],
            "startDate": startDate,
            "endDate": endDate,
            "outputFile": self.outVar.get(),
            "startingVal": self.startValVar.get(),
            "masterFigure": self.masterFigure,
            "symFigs": self.figures
        }

        # print(strat)

        if not self.indivVar.get():
            strats = {}
            for x in self.stocks:
                strats[x] = makeCustomStrategy(strat, x)

            stats = cm_backtester.backtest(**args, strats=strats)
            for k, v in stats.items():
                try:
                    self.statVars[k].set(v)
                except KeyError:
                    pass

        else:
            for x in self.stocks:
                strats = {x: makeCustomStrategy(strat, x)}
                cm_backtester.backtest(**args, strats=strats)

        for c in self.canvases:
            c.draw()

    def runAlpaca(self):
        if self.stocks is None or len(self.stocks) == 0 or len(self.stratFile) == 0:
            return

        liveRun = self.liveToggleVar.get()
        if liveRun:
            ret = messagebox.askyesno('Run LIVE Account?',
                                      'Are you sure you want to run using the LIVE (real money) account?')
            if ret is None or not ret:
                print('Cancelling Run')
                return

        with open(self.stratFile, mode='r') as f:
            strat = json.load(f)

        runTrader(stratVars=strat,
                  stocks=self.stocks,
                  liveRun=liveRun)


if __name__ == '__main__':
    from utils.run_utils import loadSystem
    loadSystem()
    app = BTGUI(tk.Tk())
    app.mainloop()
