import tkinter as tk

from cash_money import backtester_gui
from cash_money import strategy_gui

_buttons = [
    ("Strategy Maker", strategy_gui.main), ("Backtester", backtester_gui.main)
]


def main():
    root = tk.Tk()

    def cmd(func):
        root.destroy()
        func()

    for idx, btn in enumerate(_buttons):
        tk.Button(
            root, text=btn[0], command=lambda e=btn[1]: cmd(e)
        ).grid(
            row=idx, column=0, sticky='nesw'
        )

    root.mainloop()


if __name__ == "__main__":
    from cash_money.utils.run_utils import loadSystem

    loadSystem()
    main()
