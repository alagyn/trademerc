from typing import List

import imgui as im

from cash_money.trading.events import ActionEvent, CMEventListener


class ListenerGUI(CMEventListener):

    def __init__(self) -> None:
        self.actions: List[ActionEvent] = []

    def render(self):
        im.Begin("Actions")
        im.BeginListBox("Actions")
        for idx, x in enumerate(self.actions):
            im.Selectable(
                f"{idx} {x.action.stock.symbol} {x.action.action.name}"
            )
        im.EndListBox()
        im.End()

    def onAction(self, event: ActionEvent):
        self.actions.append(event)
