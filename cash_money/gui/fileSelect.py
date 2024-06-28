from typing import List, Tuple
import os

import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename


def askOpenFile(title: str, filetypes: List[Tuple[str, str]]) -> str:
    root = tk.Tk()
    root.withdraw()

    out = askopenfilename(filetypes=filetypes, title=title, parent=root)
    if out is None:
        out = ""

    root.update_idletasks()
    root.update()
    root.destroy()

    return out


def askSaveFile(title: str, startingFile: str, filetypes: List[Tuple[str, str]]) -> str:
    root = tk.Tk()
    root.withdraw()

    folder, file = os.path.split(startingFile)

    out = asksaveasfilename(
        filetypes=filetypes,
        title=title,
        parent=root,
        initialdir=folder,
        initialfile=file,
        confirmoverwrite=True,
    )
    if out is None:
        out = ""

    root.update_idletasks()
    root.update()
    root.destroy()

    return out
