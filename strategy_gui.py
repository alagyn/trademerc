import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Union

from checks import CHECKS
from cmErrors import CMError
from indicators import INDICATORS
import itertools

from objects.strategy_params import numValidate


class SerialError(CMError):
    pass


class CancelAction(CMError):
    pass


class IndicatorSerial:
    def __init__(self, name, classname, params=None):
        if params is None:
            params = {}
        self.name = name
        self.classname = classname
        self.params = params

    def toDict(self):
        return {
            'name': self.name,
            'classname': self.classname,
            'params': self.params
        }


class CheckSerial:
    def __init__(self, name, classname, indicators=None, params=None, weight=0):
        if indicators is None:
            indicators = []

        if params is None:
            params = {}

        self.name = name
        self.classname = classname
        self.indics: List[IndicRec] = [IndicRec(**x) for x in indicators]
        self.params = params
        self.weight = weight

    def toDict(self, checkInvalid=False):
        return {
            'name': self.name,
            'classname': self.classname,
            'indicators': [x.toDict(checkInvalid) for x in self.indics],
            'params': self.params,
            'weight': self.weight
        }


class IndicRec:
    def __init__(self, idx=0, key=''):
        self.idx = idx
        self.func = key

    def toDict(self, checkInvalid=False):
        if checkInvalid:
            if self.idx < 0 or len(self.func) == 0:
                raise SerialError

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

ENTRY = 0
EXIT = 1


def askOpen() -> Union[str, None]:
    # noinspection PyArgumentList
    return filedialog.askopenfilename(multiple=False, filetypes=[("JSON Strat", '.strat')])


def askSave() -> Union[str, None]:
    return filedialog.asksaveasfilename(confirmoverwrite=True, defaultextension='.strat',
                                        filetypes=[("JSON Strat", '.strat')])


def destructive(func):
    def wrapper(self: 'StrategyGUI', *args, **kwargs):
        if self.needToSave:
            try:
                self.promptSave()
            except CancelAction:
                return

        func(self, *args, **kwargs)

    return wrapper


class StrategyGUI(tk.Frame):
    def __init__(self, root):
        self.root = root
        super().__init__(root)

        self.indicList: List[IndicatorSerial] = []
        self.entryCheckList: List[CheckSerial] = []
        self.exitCheckList: List[CheckSerial] = []

        self.curSelecType = -1
        self.selection: Union[None, CheckSerial, IndicatorSerial] = None

        self.ignoreTrace = True
        self.needToSave = False

        # ROOT
        self.root.title("Strategy Designer")
        self.root.option_add('*tearOff', False)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.closeWindow)

        style = ttk.Style()

        menubar = tk.Menu(self.root)
        root['menu'] = menubar

        filemenu = tk.Menu(menubar)
        menubar.add_cascade(menu=filemenu, label='File')

        filemenu.add_command(label='Save', command=self.saveMenuCommand)
        filemenu.add_separator()
        filemenu.add_command(label='Load', command=self.loadStratFile)

        # SELF
        for x in range(4):
            self.columnconfigure(x, weight=1)

        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=1)

        self.grid(row=0, column=0, sticky='nesw')

        # INDICATORS
        # region
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

        # endregion

        # CHECKS
        # region
        def genCheckFrame(text: str, side):
            checkFrame = tk.LabelFrame(self, text=text)
            checkFrame.rowconfigure(1, weight=1)
            checkFrame.columnconfigure('all', weight=1)

            def addCommand():
                self.addCheck(side)

            def remCommand():
                self.remCheck(side)

            tk.Button(checkFrame, text='Add', command=addCommand) \
                .grid(row=0, column=0, sticky='new')

            tk.Button(checkFrame, text='Delete', command=remCommand) \
                .grid(row=0, column=1, sticky='new')

            checkListVar = tk.StringVar()

            checkListBox = tk.Listbox(checkFrame, height=10, listvariable=checkListVar,
                                      selectmode='browse', takefocus=False, exportselection=False)
            checkListBox.grid(row=1, column=0, columnspan=2, sticky='nsew')

            checkListSB = tk.Scrollbar(checkFrame, orient=tk.VERTICAL, command=checkListBox.yview)
            checkListBox.configure(yscrollcommand=checkListSB.set)
            checkListSB.grid(row=1, column=3, sticky='nse')

            checkListBox.bind('<<ListboxSelect>>', lambda e: self.selectCheck(side))

            return checkFrame, checkListVar, checkListBox

        x = genCheckFrame("Entry Checks", ENTRY)
        entryCheckFrame, self.entryCheckListVar, self.entryCheckListBox = x
        x = genCheckFrame("Exit Checks", EXIT)
        exitCheckFrame, self.exitCheckListVar, self.exitCheckListBox = x
        # endregion

        # SELECTION DETAILS
        # region
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
        self.cCheckDicts: Dict[str, List[List[int, str]]] = {}
        # noinspection PyTypeChecker
        self.cIndicCombos: Dict[str, List[ttk.Combobox]] = {}
        self.cIndicComboVars = {}
        # noinspection PyTypeChecker
        self.cIndicFuncCombos: Dict[str, List[ttk.Combobox]] = {}

        self.cWeightVar = tk.DoubleVar(value=1.0)
        self.cWeightVar.trace_add('write', self.checkModifiedWeight)

        self.selectionNB = ttk.Notebook(selectionFrame,
                                        style='Tabless.TNotebook'
                                        )
        self.selectionNB.grid(row=0, column=1, sticky='nesw')

        emptyNBFrame = tk.Frame(self.selectionNB)
        self.nbTabIDs['__EMPTY'] = 0
        self.selectionNB.add(emptyNBFrame)

        self.genISelectFrames()
        self.genCSelectFrames()
        # endregion

        # MISC
        # region
        miscFrame = tk.LabelFrame(self, text='Misc')

        etRow = 0
        tk.Label(miscFrame, text='Entry Threshold:').grid(row=etRow, column=0, sticky='nw')
        self.entryThreshVar = tk.DoubleVar(value=0.5)
        tk.Spinbox(miscFrame,
                   from_=0, to=1.0,
                   increment=0.1, textvariable=self.entryThreshVar).grid(row=etRow, column=1, sticky='nw')

        xtRow = etRow + 1
        tk.Label(miscFrame, text='Exit Threshold:').grid(row=xtRow, column=0, sticky='nw')
        self.exitThreshVar = tk.DoubleVar(value=0.5)
        tk.Spinbox(miscFrame,
                   from_=0, to=1.0,
                   increment=0.1, textvariable=self.exitThreshVar).grid(row=xtRow, column=1, sticky='nw')

        tk.Label(miscFrame).grid(row=xtRow + 1, column=0)

        stop1Row = xtRow + 2
        tk.Label(miscFrame, text='Sell-Stop Indicator:').grid(row=stop1Row, column=0, sticky='nw')
        self.stopCombo = ttk.Combobox(miscFrame, state='readonly')
        self.stopCombo.grid(row=stop1Row, column=1, sticky='nw')
        self.stopCombo.bind('<<ComboboxSelected>>', lambda e: self.stopComboModified())
        self.stopFuncVar = tk.StringVar()
        self.stopFuncCombo = ttk.Combobox(miscFrame, textvariable=self.stopFuncVar, state='readonly')
        self.stopFuncCombo.grid(row=stop1Row, column=2, sticky='nw')

        stop2Row = stop1Row + 1
        tk.Label(miscFrame, text='Scale:').grid(row=stop2Row, column=0, sticky='nw')
        self.stopScaleVar = tk.DoubleVar(value=1)
        tk.Spinbox(miscFrame,
                   from_=0, to=100, increment=0.1,
                   textvariable=self.stopScaleVar).grid(row=stop2Row, column=1, sticky='nw')

        stop3Row = stop2Row + 1
        tk.Label(miscFrame, text='Days to Update:').grid(row=stop3Row, column=0, sticky='nw')
        self.stopDaysVar = tk.IntVar(value=5)
        tk.Spinbox(miscFrame,
                   from_=1, to=100, increment=1,
                   textvariable=self.stopDaysVar).grid(row=stop3Row, column=1, sticky='nw')

        # endregion

        # MAIN GRIDDING
        indicatorFrame.grid(row=0, column=0, sticky='wnse')
        entryCheckFrame.grid(row=0, column=1, sticky='wnse')
        exitCheckFrame.grid(row=0, column=2, sticky='wnse')
        miscFrame.grid(row=0, column=3, sticky='nesw')
        self.grid_rowconfigure(1, minsize=200)
        selectionFrame.grid(row=1, column=0, columnspan=4, sticky='ewns')

        self.update()
        self.ignoreTrace = False

    @destructive
    def closeWindow(self):
        self.root.destroy()

    def updateCheckIndicLists(self):
        out = [x.name for x in self.indicList]

        for cn, combos in self.cIndicCombos.items():
            for c in combos:
                c['values'] = out

        self.stopCombo['values'] = out

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
            self.entryCheckListBox.selection_clear(0, self.entryCheckListBox.size())
            self.exitCheckListBox.selection_clear(0, self.exitCheckListBox.size())
            self.showSelectionTab(self.selection.classname)
            self.curSelecType = INDIC

            # Load params
            cn = self.selection.classname
            for k, v in self.iParamDicts[cn].items():
                try:
                    v.set(self.selection.params[k])
                except KeyError:
                    default = INDICATORS[cn].paramDict[k].default
                    v.set(default)
                    self.selection.params[k] = default

            self.update()
            self.ignoreTrace = False

    def showSelectionTab(self, classname: str):
        self.selectionNB.select(self.nbTabIDs[classname])

    def selectCheck(self, side: int):
        if side == ENTRY:
            lb = self.entryCheckListBox
            cl = self.entryCheckList
            self.exitCheckListBox.selection_clear(0, self.exitCheckListBox.size())
        else:
            lb = self.exitCheckListBox
            cl = self.exitCheckList
            self.entryCheckListBox.selection_clear(0, self.entryCheckListBox.size())

        self.indicListBox.selection_clear(0, self.indicListBox.size())

        s = lb.curselection()
        if len(s) == 1:
            if self.curSelecType != CHECK:
                self.selectionTypeCombo['values'] = check_names

            self.selection = cl[s[0]]
            self.selectionTypeVar.set(self.selection.classname)

            self.ignoreTrace = True

            cn = self.selection.classname

            # print(f'Loading: {self.selection.toDict()}')

            # Load selection indics
            for idx in range(len(self.selection.indics)):
                i = self.selection.indics[idx]
                if i.idx >= 0:
                    self.cIndicCombos[cn][idx].current(i.idx)
                    self.cIndicFuncCombos[cn][idx].set(i.func)
                else:
                    self.cIndicCombos[cn][idx].set('')
                    self.cIndicFuncCombos[cn][idx].set('')

            # Load selection params
            for key, var in self.cParamDicts[cn].items():
                try:
                    var.set(self.selection.params[key])
                except KeyError:
                    default = CHECKS[self.selection.classname].paramDict[key].default
                    var.set(default)
                    self.selection.params[key] = default

            self.cWeightVar.set(self.selection.weight)

            self.curSelecType = -1
            self.selectionNameVar.set(self.selection.name)
            self.indicListBox.selection_clear(0, self.indicListBox.size())
            self.showSelectionTab(self.selection.classname)
            self.curSelecType = CHECK

            self.ignoreTrace = False

    def updateSelectionFrame(self):
        tabID = self.nbTabIDs[self.selection.classname]
        self.selectionNB.select(tabID)

    def indicModified(self, var: str, _b, _c):
        """
        Called when an indicator var has been modified
        """
        if self.ignoreTrace:
            return

        cn, param = var.split('_')
        try:
            newVal = self.iParamDicts[cn][param].get()
        except tk.TclError:
            # TOCHANGE error?
            return

        # print(f'CN: {cn}, P:{param}, new: {newVal}')
        self.selection.params[param] = newVal

        self.needToSave = True

    def stopComboModified(self):
        if self.ignoreTrace:
            return

        indic = self.indicList[self.stopCombo.current()]
        funcs = INDICATORS[indic.classname].outputs

        self.stopFuncCombo['values'] = funcs
        self.stopFuncCombo['state'] = 'readonly'
        self.stopFuncCombo.current(0)

        self.needToSave = True

    def checkModifiedIndic(self, var: str, _b, _c):
        if self.ignoreTrace:
            return

        # its an indic or check
        cn, t, idx = var.split('_')
        idx = int(idx)

        # print(cn, t, idx)

        if t == 'validx':
            # get the combo
            combo = self.cIndicCombos[cn][idx]
            # check the new idx
            indicIdx = combo.current()

            # get the indic record
            record = self.selection.indics[idx]
            record.idx = indicIdx

            newIndic = self.indicList[indicIdx]

            funcs = INDICATORS[newIndic.classname].outputs

            # init to first func
            record.func = funcs[0]

            fCombo = self.cIndicFuncCombos[cn][idx]
            fCombo['values'] = funcs
            fCombo['state'] = 'readonly'
            fCombo.current(0)


        elif t == 'valfunc':
            newVal = self.cIndicFuncCombos[cn][idx].get()
            self.selection.indics[idx].func = newVal

        self.needToSave = True

    def checkModifiedParam(self, var: str, _b, _c):
        if self.ignoreTrace:
            return

        cn, param = var.split('_')

        try:
            newVal = self.cParamDicts[cn][param].get()
        except tk.TclError:
            # TOCHANGE error?
            return

        self.selection.params[param] = newVal
        self.needToSave = True

    def checkModifiedWeight(self, _a, _b, _c):
        if self.ignoreTrace:
            return

        try:
            self.selection.weight = self.cWeightVar.get()
        except tk.TclError:
            return

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

            # Weight
            wFrame = tk.Frame(frame)
            wFrame.grid(row=0, column=0, sticky='nesw')
            tk.Label(wFrame, text='Weight:').grid(row=0, column=0, sticky='nw')
            validate = frame.register(numValidate)
            tk.Spinbox(wFrame, textvariable=self.cWeightVar,
                       validate='key', validatecommand=(validate, '%P')
                       ).grid(row=0, column=1, sticky='nw')

            # VALS
            valFrame = tk.LabelFrame(frame, text='Indicators')
            valFrame.grid(row=1, column=0, sticky='nesw')

            iCombos = []
            iFuncCombos = []

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

                var1.trace('w', self.checkModifiedIndic)
                var2.trace('w', self.checkModifiedIndic)

            self.cIndicCombos[cn] = iCombos
            self.cIndicFuncCombos[cn] = iFuncCombos
            self.cIndicComboVars[cn] = svars

            # PARAMS

            paramFrame = tk.LabelFrame(frame, text='Parameters')
            paramFrame.grid(row=2, column=0, sticky='nesw')

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
            self.updateCheckList(ENTRY)
            self.updateCheckList(EXIT)

        self.needToSave = True

    def updateSelectedType(self):
        self.selection.classname = self.selectionTypeVar.get()
        self.updateSelectionFrame()

        self.needToSave = True

    def updateIndicList(self):
        # noinspection PyTypeChecker
        self.indicListVar.set([x.name for x in self.indicList])
        self.updateCheckIndicLists()

    def addIndic(self):
        _, name = SelectDialog(self.root, 'Select Type', indicator_names).result()

        i = IndicatorSerial(name, name)
        self.indicList.append(i)
        self.updateIndicList()

        for x in INDICATORS[name].params:
            i.params[x.paramName] = x.default

        self.needToSave = True

    def remIndic(self):
        s = self.indicListBox.curselection()
        if len(s) == 1:
            idx = s[0]
            self.indicList.pop(idx)

            for c in itertools.chain(self.entryCheckList, self.exitCheckList):
                for i in c.indics:
                    if i.idx == idx:
                        i.idx = -1
                        i.func = ''
                    elif i.idx > idx:
                        i.idx -= 1

            sCur = self.stopCombo.current()

            self.updateIndicList()

            if sCur == idx:
                self.stopCombo.set('')
                self.stopFuncVar.set('')
            elif sCur > idx:
                self.stopCombo.current(sCur - 1)

            self.needToSave = True

    def addCheck(self, side: int):
        _, name = SelectDialog(self.root, 'Select Type', check_names).result()

        if side == ENTRY:
            cl = self.entryCheckList
        else:
            cl = self.exitCheckList

        c = CheckSerial(name, name)
        cl.append(c)
        self.updateCheckList(side)

        template = CHECKS[name]

        for x in template.params:
            c.params[x.paramName] = x.default
        for x in range(template.numValFuncs):
            c.indics.append(IndicRec(-1))

        self.needToSave = True

    def remCheck(self, side: int):
        if side == ENTRY:
            lb = self.entryCheckListBox
            cl = self.entryCheckList
        else:
            lb = self.exitCheckListBox
            cl = self.exitCheckList

        s = lb.curselection()
        if len(s) == 1:
            cl.pop(s[0])
            self.updateCheckList(side)
            self.needToSave = True

    def updateCheckList(self, side: int):
        if side == ENTRY:
            var = self.entryCheckListVar
            cl = self.entryCheckList
        else:
            var = self.exitCheckListVar
            cl = self.exitCheckList

        # noinspection PyTypeChecker
        var.set([x.name for x in cl])

    def getStopParams(self):
        indic = self.stopCombo.current()
        if indic < 0:
            raise SerialError("Stop Indicator not setup")

        key = self.stopFuncVar.get()
        if len(key) == 0:
            raise SerialError("Stop Indicator value not setup")

        scale = self.stopScaleVar.get()

        return {
            'indicator': indic,
            'key': key,
            'scale': scale,
            'limitScale': 0.8,
            'daysToUpdateStop': self.stopDaysVar.get()
        }

    def saveMenuCommand(self):
        try:
            self.writeStratFile()
        except CancelAction:
            pass

    def writeStratFile(self):
        def checkChecks(l: List[CheckSerial], txt):
            _out = []
            for x in l:
                try:
                    _out.append(x.toDict(True))
                except SerialError:
                    raise SerialError(f'{txt} check not setup: {x.name}')
            return _out

        try:
            eChecks = checkChecks(self.entryCheckList, 'Entry')
            exCheck = checkChecks(self.exitCheckList, 'Exit')
            stop = self.getStopParams()
        except SerialError as err:
            messagebox.showerror('Export Error', err.msg)
            raise CancelAction

        if len(self.indicList) == 0:
            messagebox.showwarning('Export Error', 'No indicators defined')
            raise CancelAction

        if len(self.entryCheckList) == 0:
            messagebox.showwarning('Export Error', 'No entry checks defined')
            raise CancelAction

        if len(self.exitCheckList) == 0:
            messagebox.showwarning('Export Error', 'No exit checks defined')
            raise CancelAction

        out = {
            'name': "TEMP",
            'type': "Confidence",
            'indicators': [x.toDict() for x in self.indicList],
            'entryChecks': eChecks,
            'exitChecks': exCheck,
            'enterConf': self.entryThreshVar.get(),
            'exitConf': self.exitThreshVar.get(),
            'stop': stop
        }

        fn = askSave()

        if fn is not None and len(fn) > 0:
            with open(fn, mode='w') as f:
                json.dump(out, f, indent=2)

        self.needToSave = False

    @destructive
    def loadStratFile(self):
        fn = askOpen()
        if fn is None or len(fn) == 0:
            return

        try:
            with open(fn, mode='r') as f:
                d = json.load(f)
        except json.JSONDecodeError as err:
            messagebox.showerror('Import Error', f'Error loading strategy file\n{err.msg}')
            return

        self.ignoreTrace = True

        try:
            self.indicList = [IndicatorSerial(**x) for x in d['indicators']]
            self.entryCheckList = [CheckSerial(**x) for x in d['entryChecks']]
            self.exitCheckList = [CheckSerial(**x) for x in d['exitChecks']]

            self.entryThreshVar.set(d['enterConf'])
            self.exitThreshVar.set(d['exitConf'])

            self.updateIndicList()
            self.updateCheckList(ENTRY)
            self.updateCheckList(EXIT)

            self.stopCombo.current(d['stop']['indicator'])
            self.stopFuncVar.set(d['stop']['key'])
            self.stopScaleVar.set(d['stop']['scale'])
            self.stopDaysVar.set(d['stop']['daysToUpdateStop'])
        except KeyError as err:
            messagebox.showerror('Import Error', f'Error loading strategy file\nKey: {err}')
            return

        self.ignoreTrace = False

    def promptSave(self):
        ret = messagebox.askyesnocancel('Save?', 'Save Strategy?')

        if ret is None:
            raise CancelAction

        if ret:
            self.writeStratFile()


def _main():
    app = StrategyGUI(tk.Tk())
    app.mainloop()


if __name__ == '__main__':
    _main()
