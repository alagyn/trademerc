from tkinter.filedialog import askopenfilename
from tkinter.messagebox import askyesnocancel
import tkinter as tk
from cash_money.run_alpaca import runTrader

STRAT_FT = [('Strategy', '.strat')]

import threading
import time


def main():
    root = tk.Tk()
    root.withdraw()

    stratFile = askopenfilename(
        filetypes=STRAT_FT,
        title="Select Strategy",
        parent=root,
        initialdir='config'
    )
    if stratFile is None or len(stratFile) == 0:
        return

    stockFile = askopenfilename(
        filetypes=[('Text', '.txt')],
        title="Select stock list",
        parent=root,
        initialdir='config'
    )
    if stockFile is None or len(stockFile) == 0:
        return

    runPaper = askyesnocancel("Run Paper Account?", "Run Paper Account?")
    if runPaper is None:
        return

    root.update_idletasks()
    root.update()
    root.destroy()

    runTrader(stratFile=stratFile, stockFile=stockFile, liveRun=not runPaper)


if __name__ == '__main__':
    main()
