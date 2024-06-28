from cash_money.gui import cm_window
from cash_money.gui import main_ui
from cash_money.utils import run_utils


def main():
    configs = run_utils.loadSystem()
    ui = main_ui.MainUI()
    cm_window.run_window(
        "CashMoney",
        ui.render,
        init=ui.init,
        cleanup=ui.cleanup,
    )


if __name__ == '__main__':
    main()
