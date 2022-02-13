import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict

from checks import check_data
from indicators import INDICATORS


class IndicatorSerial:
    def __init__(self, name, classname):
        self.name = name
        self.classname = classname
        self.params = {}


class CheckSerial:
    def __init__(self, name, classname):
        self.name = name
        self.classname = classname
        self.indics = []
        self.checks = []
        self.params = {}




class GridDialog(tk.Toplevel):
    """
    Rewrite of simpledialog.Dialog but uses grid instead of pack
    Basic Usage: result = Subclass(args).result()
    """

    def __init__(self, parent, *, title=None, bindCancel=False):
        """
        Initializes window and waits for it to be destroyed.
        Call this AFTER doing any other setup in subclass init
        :param parent: The parent, can be none
        :param title: The title of the dialog, can be none
        :param bindCancel: If <Escape> should be bound to self.cancel
        """
        super().__init__(parent)
        self.withdraw()
        if parent.winfo_viewable():
            self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        bodyFrame = tk.Frame(self, padx=2, pady=2)
        self.body(bodyFrame)
        bodyFrame.grid()

        self.protocol('WM_DELETE_WINDOW', self.cancel)
        if bindCancel:
            self.bind('<Escape>', lambda e: self.cancel())

        if self.parent is not None:
            self.geometry(f'+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}')

        self.deiconify()

        self.focus_set()

        self.wait_visibility()
        self.grab_set()
        # Wait for self to be destroyed
        self.wait_window(self)

        self.parent.focus_force()
        self.parent.grab_set()

    def destroy(self):
        tk.Toplevel.destroy(self)

    def body(self, frame):
        raise NotImplementedError

    def cancel(self):
        raise NotImplementedError

    def result(self):
        raise NotImplementedError


class SelectDialog(GridDialog):
    def __init__(self, parent, title, vals):
        self.outidx = -1
        self.vals = vals
        self.numvals = [f'{i + 1}: {x}' for i, x in enumerate(vals)]
        # noinspection PyTypeChecker
        self.var = tk.StringVar(value=self.numvals)
        super().__init__(parent, title=title, bindCancel=True)

    def body(self, frame):
        for x in range(1, 10):
            self.bind(f'{x}', self.selectKey)

        lb = tk.Listbox(frame, listvariable=self.var, selectmode='single', )
        lb.grid(column=0, row=0, sticky='nesw')

        s = tk.Scrollbar(frame, orient=tk.VERTICAL, command=lb.yview)
        lb.configure(yscrollcommand=s.set)
        s.grid(column=1, row=0, sticky='nsw')

        lb.bind('<<ListboxSelect>>', lambda e: self.selectLB(lb))

    def selectLB(self, lb: tk.Listbox):
        self.outidx = lb.curselection()[0]
        self.destroy()

    def selectKey(self, e):
        self.outidx = int(e.keysym) - 1
        if self.outidx < len(self.vals):
            self.destroy()

    def cancel(self):
        self.outidx = -1
        self.destroy()

    def result(self):
        if self.outidx >= 0:
            return self.outidx, self.vals[self.outidx]
        else:
            raise IndexError()


indicator_names = sorted(list(INDICATORS.keys()))
check_names = sorted(list(check_data.keys()))

INDIC = 0
CHECK = 1

SELECT_GRID_LEN = 3
SELECT_PAD = 5


class StrategyGUI(tk.Frame):
    def __init__(self, root):
        self.root = root
        super().__init__(root)

        self.indicList: List[IndicatorSerial] = []
        self.checkList: List[CheckSerial] = []

        self.curSelecType = -1
        self.selection = None

        self.ignoreTrace = False

        # ROOT
        self.root.title("Strategy Designer")
        self.root.option_add('*tearOff', False)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        style = ttk.Style()

        # SELF
        for x in range(3):
            self.columnconfigure(x, weight=1)

        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=1)

        self.grid(row=0, column=0, sticky='nesw')

        # INDICATORS
        indicatorFrame = tk.LabelFrame(self, text='Indicators')
        indicatorFrame.rowconfigure(1, weight=1)
        indicatorFrame.columnconfigure('all', weight=1)

        tk.Button(indicatorFrame, text='Add', command=self.addIndic) \
            .grid(row=0, column=0, sticky='ewn')

        remIndicatorBtn = tk.Button(indicatorFrame, text='Delete', command=self.remIndic)
        remIndicatorBtn.grid(row=0, column=1, sticky='ewn')

        self.indicListVar = tk.StringVar()

        self.indicListBox = tk.Listbox(indicatorFrame, height=10, listvariable=self.indicListVar,
                                       selectmode='browse', takefocus=False, exportselection=False)
        self.indicListBox.grid(row=1, column=0, columnspan=2, sticky='nesw')

        indicListSB = tk.Scrollbar(indicatorFrame, orient=tk.VERTICAL, command=self.indicListBox.yview)
        self.indicListBox.configure(yscrollcommand=indicListSB.set)
        indicListSB.grid(row=1, column=3, sticky='nse')

        self.indicListBox.bind('<<ListboxSelect>>', lambda e: self.selectIndicator())

        # CHECKS
        checkFrame = tk.LabelFrame(self, text='Checks')
        checkFrame.rowconfigure(1, weight=1)
        checkFrame.columnconfigure('all', weight=1)

        tk.Button(checkFrame, text='Add', command=self.addCheck) \
            .grid(row=0, column=0, sticky='new')

        tk.Button(checkFrame, text='Delete', command=self.remCheck) \
            .grid(row=0, column=1, sticky='new')

        self.checkListVar = tk.StringVar()

        self.checkListBox = tk.Listbox(checkFrame, height=10, listvariable=self.checkListVar,
                                       selectmode='browse', takefocus=False, exportselection=False)
        self.checkListBox.grid(row=1, column=0, columnspan=2, sticky='nsew')

        checkListSB = tk.Scrollbar(checkFrame, orient=tk.VERTICAL, command=self.checkListBox.yview)
        self.checkListBox.configure(yscrollcommand=checkListSB.set)
        checkListSB.grid(row=1, column=3, sticky='nse')

        self.checkListBox.bind('<<ListboxSelect>>', lambda e: self.selectCheck())

        # ENTRY/EXIT
        stratFrame = tk.LabelFrame(self, text='Strategy')

        tk.Button(stratFrame, text='TEMP').grid(row=0, column=0)

        # SELECTION DETAILS
        selectionFrame = tk.LabelFrame(self, text='Selection')

        nameTypeFrame = tk.Frame(selectionFrame)
        nameTypeFrame.grid(row=0, column=0)

        tk.Label(nameTypeFrame, text='Name:').grid(row=0, column=0)
        self.selectionNameVar = tk.StringVar()
        nameEntry = tk.Entry(nameTypeFrame, textvariable=self.selectionNameVar)
        nameEntry.grid(row=0, column=1, sticky='ew')

        self.selectionNameVar.trace_add('write', self.updateSelectedName)

        tk.Label(nameTypeFrame, text='Type:').grid(row=1, column=0)

        self.selectionTypeVar = tk.StringVar()
        self.selectionTypeCombo = ttk.Combobox(nameTypeFrame, textvariable=self.selectionTypeVar)
        self.selectionTypeCombo.grid(row=1, column=1, sticky='ew')
        self.selectionTypeCombo.state(['readonly'])

        self.selectionTypeCombo.bind('<<ComboboxSelected>>', lambda e: self.updateSelectedType())

        style.layout('Tabless.TNotebook.Tab', [])

        self.nbTabIDs: Dict[str, int] = {}
        # noinspection PyTypeChecker
        self.iParamDicts: Dict[str, Dict[str, tk.Variable]] = {}
        # noinspection PyTypeChecker
        self.cParamDicts: Dict[str, Dict[str, tk.Variable]] = {}

        self.selectionNB = ttk.Notebook(selectionFrame,
                                        style='Tabless.TNotebook'
                                        )
        self.selectionNB.grid(row=0, column=1)

        emptyNBFrame = tk.Frame(self.selectionNB)
        self.nbTabIDs['__EMPTY'] = 0
        self.selectionNB.add(emptyNBFrame)

        self.genISelectFrames()
        self.genCSelectFrames()

        # TODO bind ComboboxSelected to change params

        # MAIN GRIDDING
        indicatorFrame.grid(row=0, column=0, sticky='wnse')
        checkFrame.grid(row=0, column=1, sticky='wnse')
        stratFrame.grid(row=0, column=2, sticky='wnse')
        selectionFrame.grid(row=1, column=0, columnspan=3, sticky='ewns')

    def selectIndicator(self):
        s = self.indicListBox.curselection()
        if len(s) == 1:

            self.selection = self.indicList[s[0]]

            if self.curSelecType != INDIC:
                self.selectionTypeCombo['values'] = indicator_names
            self.selectionTypeVar.set(self.selection.classname)
            # Invalidate to stop name trace callback
            self.curSelecType = -1
            self.selectionNameVar.set(self.selection.name)
            self.checkListBox.selection_clear(0, self.checkListBox.size())
            self.showSelectionTab(self.selection.classname)
            self.curSelecType = INDIC

    def showSelectionTab(self, classname: str):
        self.selectionNB.select(self.nbTabIDs[classname])

    def selectCheck(self):
        s = self.checkListBox.curselection()
        if len(s) == 1:
            if self.curSelecType != CHECK:
                self.selectionTypeCombo['values'] = check_names

            self.selection = self.checkList[s[0]]
            self.selectionTypeVar.set(self.selection.classname)
            self.curSelecType = -1
            self.selectionNameVar.set(self.selection.name)
            self.indicListBox.selection_clear(0, self.indicListBox.size())
            self.showSelectionTab(self.selection.classname)
            self.curSelecType = CHECK

    def updateSelection(self):
        if self.curSelecType < 0:
            return

        if self.curSelecType == INDIC:
            self.updateCurrentIndicator()
        elif self.curSelecType == CHECK:
            self.updateCurrentCheck()

    def updateSelectionFrame(self):
        tabID = self.nbTabIDs[self.selection.classname]
        self.selectionNB.select(tabID)

    def indicModified(self, var: str, _b, _c):
        if self.ignoreTrace:
            return

        cn, param = var.split('_')
        try:
            newVal = self.iParamDicts[cn][param].get()
        except tk.TclError:
            # TODO error?
            return

        print(f'CN: {cn}, P:{param}, new: {newVal}')
        self.selection.params[param] = newVal

    def genISelectFrames(self):
        for cn, iType in INDICATORS.items():
            nextID = len(self.nbTabIDs)
            frame = tk.LabelFrame(self.selectionNB, text=cn)

            self.nbTabIDs[cn] = nextID
            self.selectionNB.add(frame)

            params: Dict[str, tk.Variable] = {}
            self.iParamDicts[cn] = params
            x = 0
            y = 0

            for paramdata in iType.params:
                f = tk.Frame(frame)
                f.grid(row=y, column=x, sticky='nesw')

                var = paramdata.render(f)
                var.trace_add('write', self.indicModified)

                params[paramdata.paramName] = var

                x += 1
                if x >= SELECT_GRID_LEN:
                    x = 0
                    y += 1

    def genCSelectFrames(self):
        # TODO
        pass

    def updateSelectedName(self, _1, _2, _3):
        self.selection.name = self.selectionNameVar.get()
        if self.curSelecType == INDIC:
            self.updateIndicList()
        elif self.curSelecType == CHECK:
            self.updateCheckList()

    def updateSelectedType(self):
        self.selection.classname = self.selectionTypeVar.get()
        self.updateSelectionFrame()

    def updateCurrentIndicator(self):
        self.ignoreTrace = True

        s = self.indicListBox.curselection()
        if len(s) == 1:
            i = self.indicList[s[0]]
            i.name = self.selectionNameVar.get()

            for name, var in self.iParamDicts[i.classname].values():
                i.params[name] = var.get()

        self.updateIndicList()

        self.ignoreTrace = False

    def updateCurrentCheck(self):
        # TODO
        pass

    def updateIndicList(self):
        # noinspection PyTypeChecker
        self.indicListVar.set([x.name for x in self.indicList])

    def addIndic(self):
        _, name = SelectDialog(self.root, 'Select Type', indicator_names).result()
        self.indicList.append(IndicatorSerial(name, name))
        self.updateIndicList()

    def remIndic(self):
        s = self.indicListBox.curselection()
        if len(s) == 1:
            self.indicList.pop(s[0])
            self.updateIndicList()

    def addCheck(self):
        _, name = SelectDialog(self.root, 'Select Type', check_names).result()
        self.checkList.append(CheckSerial(name, name))
        self.updateCheckList()

    def remCheck(self):
        s = self.checkListBox.curselection()
        if len(s) == 1:
            self.checkList.pop(s[0])
            self.updateCheckList()

    def updateCheckList(self):
        # noinspection PyTypeChecker
        self.checkListVar.set([x.name for x in self.checkList])


def _main():
    app = StrategyGUI(tk.Tk())
    app.mainloop()


if __name__ == '__main__':
    _main()
