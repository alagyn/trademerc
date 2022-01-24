import datetime
import os.path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from tkcalendar import DateEntry
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import cm_backtester
from utils.file_utils import loadStratFile, loadStockFile
from utils.api_utils import loadPaperAPI
from consts import STRAT_FORMAT, DATE_FMT
from cmErrors import StrategyError
from strategies.hardStrategy import HardStrategy
from run_alpaca import runTrader


def makeLabelEntry(p, text, loc, vartype=str):
    label = tk.Label(p, text=text, anchor='e')

    # TODO entry validation

    if vartype == str:
        var = tk.StringVar()
    elif vartype == int:
        var = tk.IntVar()
    elif vartype == float:
        var = tk.DoubleVar()
    else:
        raise TypeError("Invalid vartype")

    entry = tk.Entry(p, textvariable=var)
    label.grid(column=loc[0], row=loc[1], sticky='ew')
    entry.grid(column=loc[0] + 1, row=loc[1], sticky='ew', padx=5, pady=2)

    return var


def recursAdd(frame: tk.Frame, key: str, x, row: int, textVars):
    FRAME_PAD = 3

    if isinstance(x, dict):
        if len(key) > 0:
            label = tk.LabelFrame(frame, text=(key + ":"))
            label.grid(row=row, column=0, columnspan=2, padx=FRAME_PAD, pady=FRAME_PAD, sticky='ew')
            row += 1
            newVars = {}
            textVars[key] = newVars
        else:
            label = frame
            newVars = textVars

        for key, val in x.items():
            row = recursAdd(label, key, val, row, newVars)

        return row
    else:
        textVars[key] = makeLabelEntry(frame, key + ":", (0, row), type(x))
        return row + 1


def recurseLoadStrat(tkVars, strat):
    for key, val in tkVars.items():
        if isinstance(val, dict):
            varDict = tkVars[key]
            stratDict = strat[key]
            recurseLoadStrat(varDict, stratDict)
        else:
            val.set(strat[key])


def genStrategyFrame(frame):
    f = open(STRAT_FORMAT, mode='r')
    fmt = json.load(f)
    f.close()
    textVars = {}
    recursAdd(frame, "", fmt, 0, textVars)
    return textVars


def recursBuildStrat(textvars: dict, out):
    for key, val in textvars.items():
        if isinstance(val, dict):
            newDict = {}
            out[key] = newDict
            recursBuildStrat(val, newDict)
        else:
            out[key] = val.get()


class BTGUI(tk.Frame):
    def __init__(self, root):
        self.root = root
        super().__init__(self.root)

        self.root.protocol("WM_DELETE_WINDOW", self.closeWindow)

        self.stocks = []

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

        # RUN FRAME
        runFrame = tk.LabelFrame(self, text="Run")

        LOAD_BTN_ROW = 0

        loadStratBtn = tk.Button(runFrame, text='Load Strategy', command=self.selectStrat)
        loadStratBtn.grid(row=LOAD_BTN_ROW, column=0, columnspan=2, sticky='ew', padx=5, pady=2)

        '''
        SAVE_BTN_ROW = LOAD_BTN_ROW + 1

        saveStratBtn = tk.Button(runFrame, text='Save Strategy', command=self.saveStrat)
        saveStratBtn.grid(row=SAVE_BTN_ROW, column=0, columnspan=2, sticky='ew', padx=5, pady=2)
        '''

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

        # STRATEGY FRAME
        stratFrame = tk.LabelFrame(self, text="Strategy")
        stratFrame.columnconfigure(0, weight=1)

        self.stratVars = genStrategyFrame(stratFrame)

        ttk.Separator(runFrame, orient=tk.HORIZONTAL).grid(row=RUN_BTN_ROW + 1, column=0,
                                                           columnspan=2, sticky='ew',
                                                           pady=10)

        # GRID MAIN FRAMES
        FRAME_PAD = 5

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
        mainGraphFrame.grid(row=0, column=1, sticky='news', padx=FRAME_PAD)
        # stratFrame.grid(row=0, column=1, sticky='nsew', padx=FRAME_PAD)

    def closeWindow(self):
        self.root.destroy()

    def selectOut(self):
        ret = filedialog.askopenfilename(filetypes=[('json', 'json')], multiple=False, initialdir='.')
        if len(ret) > 0:
            self.outVar.set(ret)

    def selectStrat(self):
        ret = filedialog.askopenfilename(filetypes=[('json', 'json')], multiple=False, initialdir='./config')
        if len(ret) > 0:
            try:
                strat = loadStratFile(ret)
                recurseLoadStrat(self.stratVars, strat)
                self.stratNameVar.set(strat['name'])
            except StrategyError as err:
                messagebox.showerror("Strategy Error", str(err))

    def selectSymbolFile(self):
        ret = filedialog.askopenfilename(filetypes=[('.txt', '.txt')], multiple=False, initialdir='./config')
        if len(ret) > 0:
            self.stocks = loadStockFile(ret)
            _, f = os.path.split(ret)
            self.symbolVar.set(f)

            self.genGraphs()

    def saveStrat(self):
        strat = self.buildStrat()

        ret = filedialog.asksaveasfilename(filetypes=[('json', 'json')], confirmoverwrite=True,
                                           defaultextension='.json')

        if len(ret) > 0:
            with open(ret, mode='w') as f:
                json.dump(strat, f)

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

    def buildStrat(self):
        strat = {}
        recursBuildStrat(self.stratVars, strat)
        return strat

    def runBT(self):
        if len(self.stocks) <= 0:
            return

        strat = self.buildStrat()

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
                strats[x] = HardStrategy(x, strat)

            cm_backtester.backtest(**args, strats=strats)

        else:
            for x in self.stocks:
                strats = {x: HardStrategy(x, strat)}
                cm_backtester.backtest(**args, strats=strats)

        for c in self.canvases:
            c.draw()

    def runAlpaca(self):
        if self.stocks is None:
            return

        liveRun = self.liveToggleVar.get()
        if liveRun:
            ret = messagebox.askyesno('Run LIVE Account?',
                                      'Are you sure you want to run using the LIVE (real money) account?')
            if ret is None or not ret:
                print('Cancelling Run')
                return

        runTrader(stratVars=self.buildStrat(),
                  stocks=self.stocks,
                  liveRun=liveRun)


if __name__ == '__main__':
    app = BTGUI(tk.Tk())
    app.mainloop()
