import json
import tkinter as tk
from tkinter import filedialog

from nodepasta.argtypes import FLOAT, BOOL
from nodepasta.errors import NodeGraphError
from nodepasta.nodegraph import NodeGraph
from nodepasta.tk.tk_node_graph import TKNodeGraph

from cash_money.utils.node_utils import registerNodes

if __name__ == '__main__':
    ng = NodeGraph()

    registerNodes(ng)

    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=0)
    root.rowconfigure(1, weight=1)

    canvasFrame = tk.LabelFrame(root, text='CANVAS')
    canvasFrame.grid(row=1, column=0, sticky='nesw')

    canvasFrame.columnconfigure(0, weight=1)
    canvasFrame.rowconfigure(0, weight=1)


    ngFrame = TKNodeGraph(canvasFrame, ng)
    ngFrame.setPortTypeColor(FLOAT, "lightgreen")
    ngFrame.setPortTypeColor(BOOL, "brown")

    def load():
        filename = filedialog.askopenfilename(filetypes=[(".strat", ".strat")], defaultextension="strat")
        if filename is not None and len(filename) > 0:
            with open(filename, mode='r') as f:
                data = json.load(f)
            try:
                ng.loadFromJSON(data['graph'])
                ngFrame.reset()
                ngFrame.reloadGraph()
            except NodeGraphError as err:
                print("ERROR:", str(err))
                exit()

    ngFrame.grid(row=0, column=0, sticky='nesw')


    def execute():
        try:
            ng.execute()
        except NodeGraphError as e:
            # Set an error message in the info box
            ngFrame.setErrorMessage(f'{e.loc}: {e.msg}')


    btnFrame = tk.LabelFrame(root, text='')
    btnFrame.grid(row=0, column=0, sticky='nw')


    def save():
        ret = filedialog.asksaveasfilename(confirmoverwrite=True, filetypes=[(".strat", ".strat")],
                                           defaultextension=".json")
        if ret is not None and len(ret) > 0:
            print(f"Saving to {ret}")
            graph = ng.getJSON()
            out = {
                "graph": graph,
                "name": "STRATEGY"
            }
            with open(ret, mode='w') as f:
                json.dump(out, f)

    tk.Button(btnFrame, text="Load", command=load).grid(row=0, column=0, sticky='w')
    tk.Button(btnFrame, text='Save', command=save).grid(row=0, column=1, stick='w')

    root.wm_state('zoomed')

    root.mainloop()
