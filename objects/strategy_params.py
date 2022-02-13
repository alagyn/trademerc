import re
from typing import List, Any

from cmErrors import IndicatorError
import tkinter as tk
from tkinter import ttk


class Param:
    def __init__(self, paramName: str, displayName: str, datatype: type, default: Any):
        self.datatype = datatype
        self.displayName = displayName
        self.paramName = paramName
        if not isinstance(default, datatype):
            raise IndicatorError("DEVERR: Defualt indicator param value is wrong type"
                                 f"Expected: {datatype.__name__}, got {type(default)}: '{default}'")
        self.default: Any = default
        self.parentName = "ERROR"

    def render(self, frame: tk.Frame) -> tk.Variable:
        raise NotImplementedError

    def getVarName(self):
        return f'{self.parentName}_{self.paramName}'


INT_RE = re.compile(r'-?\d*')


def _intValidate(i: str) -> bool:
    return INT_RE.fullmatch(i) is not None


NUM_RE = re.compile(r'-?\d*([.]\d*)?')


def _numValidate(i: str) -> bool:
    return NUM_RE.fullmatch(i) is not None


class NumberParam(Param):
    def __init__(self, paramName: str, displayName: str, datatype: type, default):
        super().__init__(paramName, displayName, datatype, default)

    def render(self, frame: tk.Frame) -> tk.Variable:

        if self.datatype == int:
            var = tk.IntVar(value=self.default, name=self.getVarName())
            validate = frame.register(_intValidate)
        else:
            var = tk.DoubleVar(value=self.default, name=self.getVarName())
            validate = frame.register(_numValidate)

        tk.Label(frame, text=f'{self.displayName}:').grid(row=0, column=0, sticky='nesw')

        tk.Spinbox(frame, textvariable=var, validate='key', validatecommand=(validate, '%P')).grid(row=0, column=1,
                                                                                                   sticky='nesw')

        return var


class ComboSelector(Param):
    def __init__(self, paramName: str, displayName: str, choices: List[str], default: str):
        super().__init__(paramName, displayName, str, default)
        self.choices = choices

    def render(self, frame: tk.Frame) -> tk.Variable:
        var = tk.StringVar(value=self.default, name=self.getVarName())

        # TODO label text
        tk.Label(frame, text=f'{self.displayName}:').grid(row=0, column=0, sticky='nesw')
        ttk.Combobox(frame, textvariable=var,
                     values=self.choices,
                     state="readonly").grid(row=0, column=1,
                                            sticky='nesw')

        return var


class DataSelector(ComboSelector):
    def __init__(self):
        super().__init__("data", "Bar", ["Low", "Close", "High"], 'Close')
