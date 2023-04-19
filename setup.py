import os.path
import os
from typing import List, Tuple

from cx_Freeze import setup, Executable

LOGO = "docs/CashMoneyLogo.ico"

include_files: List[Tuple[str, str]] = [
    ("LICENSE", "LICENSE"),
    ("config/example_system.cfg", "config/system.cfg"),
    ("config/example_strat.strat", "config/example_strat.strat"),
    ("config/example_stocks.txt", "config/example_stocks.txt")
]

options = {
    "build_exe": {
        "includes": "cash_money",
        "excludes":
        "pyarrow,alabaster,altgraph,bcrypt,cloudpickle,PyQt5,sphinx,setuptools",
        "include_files": include_files
    }
}

executables = [
    Executable("cash_money/backtester_gui.py", base="", icon=LOGO),
    Executable("cash_money/strategy_gui.py", base="Win32GUI", icon=LOGO)
]

setup(
    name="cashmoney",
    version="0.2.2",
    description="Backtesting and Live Trading Application",
    options=options,
    executables=executables
)
