import imgui as im

from ..ui_state import UIState


class StrategyTab:

    def __init__(self) -> None:
        pass

    def render(self, state: UIState):
        if im.Button("Load Strategy"):
            state.askStrat()
        im.SameLine()
        im.Text(state.stratFile)
        if im.Button("New"):
            state.newStrat()
        im.SameLine()
        if im.Button("Save"):
            state.saveStrat()
        im.SameLine()
        if im.Button("Save As"):
            state.askSaveStrat()

        io = im.GetIO()

        if io.KeyCtrl and im.IsKeyPressed(im.ImKey.S, repeat=False):
            print("Saving")
            state.saveStrat()

        state.imNodeGraph.render()
