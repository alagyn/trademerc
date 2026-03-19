import imgui as im

from .ui_state import UIState
from .tabs.backtesterTab import BacktesterTab
from .tabs.strategyTab import StrategyTab
from .tabs.configTab import ConfigTab
from cash_money.utils.run_utils import _configLoc

windowFlags = (
    im.WindowFlags.NoMove
    | im.WindowFlags.NoResize
    | im.WindowFlags.NoCollapse
    | im.WindowFlags.NoDecoration
)


class MainUI:

    def __init__(self) -> None:
        self.state = UIState()

        # Tabs
        self.backtesterTab = BacktesterTab()
        self.strategyTab = StrategyTab()
        self.configTab = ConfigTab(_configLoc)
    def init(self):
        self.state.init()

    def cleanup(self):
        self.state.toCache()
        if self.needToSave():
            self.state.askSaveStrat()

    def needToSave(self) -> bool:
        return self.state.imNodeGraph is not None and self.state.imNodeGraph.needToSave

    def render(self) -> bool:
        self._renderMenuBar()

        vp = im.GetMainViewport()
        im.SetNextWindowPos(vp.WorkPos)
        im.SetNextWindowSize(vp.WorkSize)
        if im.Begin("##main", flags=windowFlags):
            if im.BeginTabBar("_mainTabs"):

                if im.BeginTabItem("Backtesting"):
                    self.backtesterTab.render(self.state)
                    im.EndTabItem()

                if im.BeginTabItem(f"Strategy{' *' if self.needToSave() else ''}###strategy"):
                    self.strategyTab.render(self.state)
                    im.EndTabItem()

                if im.BeginTabItem("Config"):
                    self.configTab.render()
                    im.EndTabItem()

                im.EndTabBar()
        im.End()

        return False

    def _renderMenuBar(self) -> None:
        if im.BeginMainMenuBar():
            if im.BeginMenu("File"):
                if im.MenuItem("Test"):
                    print("test")
                im.EndMenu()

            im.EndMainMenuBar()
