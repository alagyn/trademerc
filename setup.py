import os.path
import os
from typing import List, Tuple

from cx_Freeze import setup, Executable

include_files: List[Tuple[str, str]] = [("LICENSE", "LICENSE")]

for x in os.listdir("config"):
    if x.startswith("example_"):
        path = os.path.join("config", x)
        include_files.append((os.path.abspath(path), path))

options = {
    "build_exe": {
        "includes": "cash_money",
        "excludes": "pyarrow,alabaster,altgraph,bcrypt,cloudpickle,PyQt5,sphinx,setuptools",

        "include_files": include_files
    }
}

executables = [
    Executable("cash_money/backtester_gui.py", base=""),
    Executable("cash_money/strategy_gui.py", base="Win32GUI")
]

setup(
    name="cashmoney",
    version="0.2.1",
    description="Backtesting and Live Trading Application",
    options=options,
    executables=executables
)
