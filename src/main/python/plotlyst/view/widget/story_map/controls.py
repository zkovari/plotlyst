"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

This file is part of Plotlyst.

Plotlyst is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Plotlyst is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon, QShowEvent
from PyQt6.QtWidgets import QLabel, QButtonGroup, QToolButton, QFrame
from overrides import overrides
from qthandy import grid

from src.main.python.plotlyst.view.common import shadow, tool_btn
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.story_map.items import ItemType


class SecondarySelectorWidget(QFrame):
    selected = pyqtSignal(ItemType)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty('relaxed-white-bg', True)
        self.setProperty('rounded', True)
        shadow(self)
        self._grid = grid(self)

        self._btnGroup = QButtonGroup()

    def _newButton(self, itemType: ItemType, icon: QIcon, tooltip: str, row: int, col: int) -> QToolButton:
        def clicked(toggled: bool):
            if toggled:
                self.selected.emit(itemType)

        btn = tool_btn(icon, tooltip,
                       True, icon_resize=False,
                       properties=['transparent-rounded-bg-on-hover', 'top-selector'],
                       parent=self)

        self._btnGroup.addButton(btn)
        self._grid.layout().addWidget(btn, row, col)
        btn.clicked.connect(clicked)

        return btn


class EventSelectorWidget(SecondarySelectorWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid.addWidget(QLabel('Events'), 0, 0, 1, 3)

        self._btnGeneral = self._newButton(ItemType.EVENT, IconRegistry.from_name('mdi.square-rounded-outline'),
                                           'General event', 1, 0)
        self._btnGoal = self._newButton(ItemType.GOAL, IconRegistry.goal_icon('black', 'black'), 'Add new goal', 1, 1)
        self._btnConflict = self._newButton(ItemType.CONFLICT, IconRegistry.conflict_icon('black', 'black'),
                                            'Conflict', 1, 2)
        self._btnDisturbance = self._newButton(ItemType.DISTURBANCE, IconRegistry.inciting_incident_icon('black'),
                                               'Inciting incident', 2,
                                               0)
        self._btnBackstory = self._newButton(ItemType.BACKSTORY, IconRegistry.backstory_icon('black', 'black'),
                                             'Backstory', 2, 1)

        self._grid.addWidget(QLabel('Narrative'), 3, 0, 1, 3)
        self._btnQuestion = self._newButton(ItemType.QUESTION, IconRegistry.from_name('ei.question-sign'),
                                            "Reader's question", 4,
                                            0)
        self._btnSetup = self._newButton(ItemType.SETUP, IconRegistry.from_name('ri.seedling-fill'),
                                         'Setup and payoff', 4, 1)
        self._btnForeshadowing = self._newButton(ItemType.FORESHADOWING, IconRegistry.from_name('mdi6.crystal-ball'),
                                                 'Foreshadowing',
                                                 4,
                                                 2)

        self._btnGeneral.setChecked(True)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        self._btnGeneral.setChecked(True)


class StickerSelectorWidget(SecondarySelectorWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._btnComment = self._newButton(ItemType.COMMENT, IconRegistry.from_name('mdi.comment-text-outline'),
                                           'Add new comment', 0, 0)
        self._btnTool = self._newButton(ItemType.TOOL, IconRegistry.tool_icon('black', 'black'), 'Add new tool', 0, 1)
        self._btnCost = self._newButton(ItemType.COST, IconRegistry.cost_icon('black', 'black'), 'Add new cost', 1, 0)

        self._btnComment.setChecked(True)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        self._btnComment.setChecked(True)