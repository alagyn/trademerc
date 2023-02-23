from tkinter.filedialog import askopenfilename
from tkinter.messagebox import askyesnocancel

from cash_money.run_alpaca import runTrader

STRAT_FT = [('Strategy', '.strat')]


def main():
    stratFile = askopenfilename(
        filetypes=STRAT_FT,
        title="Select Strategy"
    )
    if stratFile is None or len(stratFile) == 0:
        return

    stockFile = askopenfilename(
        filetypes=[('Text', '.txt')],
        title="Select stock list"
    )
    if stockFile is None or len(stockFile) == 0:
        return

    runPaper = askyesnocancel("Run Paper Account?", "Run Paper Account?")
    if runPaper is None:
        return

    runTrader(stratFile=stratFile,
              stockFile=stockFile, liveRun=not runPaper)


if __name__ == '__main__':
    main()
