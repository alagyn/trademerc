import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Tuple, Union

from checks import CHECKS
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
        self.indics: List[IndicRec] = []
        self.checks = []
        self.params = {}

    def toDict(self):
        return {
            'name': self.name,
            'class': self.classname,
            'indicators': [x.toDict() for x in self.indics],
            'params': self.params
        }


class IndicRec:
    def __init__(self, idx=0, func=''):
        self.idx = idx
        self.func = func

    def toDict(self):
        return {'idx': self.idx, 'key': self.func}

    def copy(self):
        return IndicRec(self.idx, self.func)

    def paste(self, o: 'IndicRec'):
        self.idx = o.idx
        self.func = o.func


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
check_names = sorted(list(CHECKS.keys()))

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
        self.selection: Union[None, CheckSerial, IndicatorSerial] = None

        self.ignoreTrace = True

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
        selectionFrame.rowconfigure(0, weight=1)
        selectionFrame.columnconfigure(1, weight=1)

        nameTypeFrame = tk.Frame(selectionFrame)
        nameTypeFrame.grid(row=0, column=0, sticky='nesw')

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
        # noinspection PyTypeChecker
        self.cIndicRecs: Dict[str, List[IndicRec]] = {}
        # noinspection PyTypeChecker
        self.cCheckDicts: Dict[str, List[List[int, str]]] = {}
        # noinspection PyTypeChecker
        self.cIndicCombos: Dict[str, List[ttk.Combobox]] = {}
        self.cIndicComboVars = {}
        # noinspection PyTypeChecker
        self.cIndicFuncCombos: Dict[str, List[ttk.Combobox]] = {}

        self.selectionNB = ttk.Notebook(selectionFrame,
                                        style='Tabless.TNotebook'
                                        )
        self.selectionNB.grid(row=0, column=1, sticky='nesw')

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
        self.grid_rowconfigure(1, minsize=200)
        selectionFrame.grid(row=1, column=0, columnspan=3, sticky='ewns')

        self.ignoreTrace = False

    def updateCheckIndicLists(self):
        out = [x.name for x in self.indicList]

        for cn, combos in self.cIndicCombos.items():
            for c in combos:
                c['values'] = out

    def selectIndicator(self):
        s = self.indicListBox.curselection()
        if len(s) == 1:

            self.selection = self.indicList[s[0]]

            if self.curSelecType != INDIC:
                self.selectionTypeCombo['values'] = indicator_names
            self.selectionTypeVar.set(self.selection.classname)

            self.ignoreTrace = True

            self.curSelecType = -1
            self.selectionNameVar.set(self.selection.name)
            self.checkListBox.selection_clear(0, self.checkListBox.size())
            self.showSelectionTab(self.selection.classname)
            self.curSelecType = INDIC

            # TODO load params

            self.ignoreTrace = False

    def showSelectionTab(self, classname: str):
        self.selectionNB.select(self.nbTabIDs[classname])

    def selectCheck(self):
        s = self.checkListBox.curselection()
        if len(s) == 1:
            if self.curSelecType != CHECK:
                self.selectionTypeCombo['values'] = check_names

            if self.selection is not None:
                cn = self.selection.classname
                self.selection.indics = [x.copy() for x in self.cIndicRecs[cn]]

            self.selection = self.checkList[s[0]]
            self.selectionTypeVar.set(self.selection.classname)

            self.ignoreTrace = True

            cn = self.selection.classname
            if len(self.selection.indics) > 0:
                for idx in range(len(self.cIndicRecs[cn])):
                    i = self.selection.indics[idx]
                    self.cIndicRecs[cn][idx].paste(i)
                    self.cIndicCombos[cn][idx].current(i.idx)
                    self.cIndicFuncCombos[cn][idx].set(i.func)

            for key, val in self.selection.params.items():
                self.cParamDicts[cn][key].set(val)

            self.curSelecType = -1
            self.selectionNameVar.set(self.selection.name)
            self.indicListBox.selection_clear(0, self.indicListBox.size())
            self.showSelectionTab(self.selection.classname)
            self.curSelecType = CHECK

            self.ignoreTrace = False

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

    def checkModifiedIndic(self, var: str, _b, _c):
        if self.ignoreTrace:
            return

        # its an indic or check
        cn, t, idx = var.split('_')
        idx = int(idx)

        if t == 'validx':
            combo = self.cIndicCombos[cn][idx]
            indicIdx = combo.current()
            self.cIndicRecs[cn][idx].idx = indicIdx

            newIndic = self.indicList[indicIdx]

            funcs = INDICATORS[newIndic.classname].outputs

            fCombo = self.cIndicFuncCombos[cn][idx]
            fCombo['values'] = funcs
            fCombo['state'] = 'readonly'
            fCombo.current(0)


        elif t == 'valfunc':
            newVal = self.cIndicFuncCombos[cn][idx].get()
            self.cIndicRecs[cn][idx].func = newVal

    def checkModifiedParam(self, var: str, _b, _c):
        if self.ignoreTrace:
            return

        cn, param = var.split('_')

        try:
            newVal = self.cParamDicts[cn][param].get()
        except tk.TclError:
            # TODO error?
            return

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
        for cn, cType in CHECKS.items():
            nextID = len(self.nbTabIDs)
            frame = tk.LabelFrame(self.selectionNB, text=cn)

            self.nbTabIDs[cn] = nextID
            self.selectionNB.add(frame)

            params: Dict[str, tk.Variable] = {}
            self.cParamDicts[cn] = params

            # VALS
            valFrame = tk.LabelFrame(frame, text='Indicators')
            valFrame.grid(row=0, column=0, sticky='nesw')

            iCombos = []
            iFuncCombos = []

            indicRecs = []
            svars = {}

            for i in range(cType.numValFuncs):
                tk.Label(valFrame, text=f'{i + 1}:').grid(row=i, column=0, sticky='nwe')

                varname1 = f'{cn}_validx_{i}'
                var1 = tk.StringVar(value='', name=varname1)
                c1 = ttk.Combobox(valFrame, values=[], state='readonly', textvariable=var1)
                c1.grid(row=i, column=1, sticky='nw')

                iCombos.append(c1)

                svars[varname1] = var1

                varname2 = f'{cn}_valfunc_{i}'
                var2 = tk.StringVar(value='', name=varname2)
                c2 = ttk.Combobox(valFrame, values=[], state='disabled', textvariable=var2)
                c2.grid(row=i, column=3, sticky='nw')

                svars[varname2] = var2

                iFuncCombos.append(c2)

                indicRecs.append(IndicRec())

                var1.trace('w', self.checkModifiedIndic)
                var2.trace('w', self.checkModifiedIndic)

            self.cIndicCombos[cn] = iCombos
            self.cIndicFuncCombos[cn] = iFuncCombos
            self.cIndicRecs[cn] = indicRecs
            self.cIndicComboVars[cn] = svars

            # PARAMS

            paramFrame = tk.LabelFrame(frame, text='Parameters')
            paramFrame.grid(row=1, column=0, sticky='nesw')

            x = 0
            y = 0

            for paramdata in cType.params:
                f = tk.Frame(paramFrame)
                f.grid(row=y, column=x, sticky='nesw')

                var = paramdata.render(f)
                var.trace_add('write', self.checkModifiedParam)

                params[paramdata.paramName] = var

                x += 1
                if x >= SELECT_GRID_LEN:
                    x = 0
                    y += 1

    def updateSelectedName(self, _1, _2, _3):
        if self.ignoreTrace:
            return

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
        self.updateCheckIndicLists()

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
