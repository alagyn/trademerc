import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import backtester
import json
from consts import STRAT_FORMAT, DATE_FMT
from cmErrors import StrategyError
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


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
    def __init__(self):
        self.root = tk.Tk()
        super().__init__(self.root)

        self.root.protocol("WM_DELETE_WINDOW", self.closeWindow)

        self.stocks = []

        # ROOT
        self.root.title("Backtester")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.grid(column=0, row=0, sticky='nesw')
        for x in range(3):
            self.columnconfigure(x, weight=1)

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

        '''
        tk.Label(runFrame, text='Symbol:').grid(row=SYMBOL_IN_ROW, column=0, padx=2)
        self.symbolVar = tk.StringVar()
        symbolEntry = tk.Entry(runFrame, textvariable=self.symbolVar)
        symbolEntry.grid(row=SYMBOL_IN_ROW, column=1, padx=2)
        '''

        SEP1_ROW = SYMBOL_IN_ROW + 1

        ttk.Separator(runFrame, orient=tk.HORIZONTAL).grid(row=SEP1_ROW, column=0,
                                                           columnspan=2, sticky='ew',
                                                           pady=10)

        START_DATE_ROW = SEP1_ROW + 1

        startLabel = tk.Label(runFrame, text='Start Date:')
        startLabel.grid(row=START_DATE_ROW, column=0, sticky='ew')

        self.startInput = DateEntry(runFrame)
        self.startInput.grid(row=START_DATE_ROW, column=1, sticky='ew', padx=5)
        self.startInput.set_date(datetime.datetime(2018, 1, 1))

        END_DATE_ROW = START_DATE_ROW + 1

        endLabel = tk.Label(runFrame, text='End Date:')
        endLabel.grid(row=END_DATE_ROW, column=0, sticky='ew')

        self.endInput = DateEntry(runFrame)
        self.endInput.grid(row=END_DATE_ROW, column=1, sticky='ew', padx=5)
        self.endInput.set_date(datetime.datetime.today())

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

        RUN_BTN_ROW = OUT_BTN_ROW + 1

        runBtn = tk.Button(runFrame, text='Run Backtest', command=self.runBT)
        runBtn.grid(row=RUN_BTN_ROW, column=0, columnspan=2, sticky='ew', padx=5)

        # STRATEGY FRAME
        stratFrame = tk.LabelFrame(self, text="Strategy")
        stratFrame.columnconfigure(0, weight=1)

        self.stratVars = genStrategyFrame(stratFrame)

        # GRID MAIN FRAMES
        FRAME_PAD = 5

        runFrame.grid(row=0, column=0, sticky='nsew', padx=FRAME_PAD)
        # stratFrame.grid(row=0, column=1, sticky='nsew', padx=FRAME_PAD)


    def closeWindow(self):
        self.root.destroy()

    def selectOut(self):
        ret = filedialog.askopenfilename(filetypes=[('json', 'json')], multiple=False, initialdir='.')
        if len(ret) > 0:
            self.outVar.set(ret)

    def selectStrat(self):
        ret = filedialog.askopenfilename(filetypes=[('json', 'json')], multiple=False, initialdir='.')
        if len(ret) > 0:
            try:
                strat = backtester.loadStratFile(ret)
                recurseLoadStrat(self.stratVars, strat)
                self.stratNameVar.set(strat['name'])
            except StrategyError as err:
                messagebox.showerror("Strategy Error", str(err))

    def selectSymbolFile(self):
        ret = filedialog.askopenfilename(filetypes=[('.txt', '.txt')], multiple=False, initialdir='.')
        if len(ret) > 0:
            self.stocks = backtester.loadStockFile(ret)

    def saveStrat(self):
        strat = self.buildStrat()

        ret = filedialog.asksaveasfilename(filetypes=[('json', 'json')], confirmoverwrite=True,
                                           defaultextension='.json')

        if len(ret) > 0:
            with open(ret, mode='w') as f:
                json.dump(strat, f)

    def buildStrat(self):
        strat = {}
        recursBuildStrat(self.stratVars, strat)
        return strat

    def runBT(self):
        strat = self.buildStrat()

        startDate = self.startInput.get_date().strftime(DATE_FMT)
        endDate = self.endInput.get_date().strftime(DATE_FMT)

        backtester.backtest(self.stocks, strat, startDate, endDate, self.outVar.get(),
                            startingVal=self.startValVar.get())



if __name__ == '__main__':
    app = BTGUI()
    app.mainloop()
