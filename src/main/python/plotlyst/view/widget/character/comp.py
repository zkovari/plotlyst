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
from enum import Enum
from typing import Dict

from PyQt6 import sip
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel
from qthandy import vbox, hbox, line, flow

from src.main.python.plotlyst.core.domain import Character
from src.main.python.plotlyst.view.icons import set_avatar
from src.main.python.plotlyst.view.widget.big_five import BigFiveChart, dimension_from
from src.main.python.plotlyst.view.widget.display import RoleIcon, ChartView


class CharacterOverviewWidget(QWidget):
    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self._character = character

        self._avatar = QLabel(self)
        set_avatar(self._avatar, self._character, size=118)
        self._roleIcon = RoleIcon(self)
        if self._character.role:
            self._roleIcon.setRole(self._character.role, showText=True)

        vbox(self, 0)
        self.layout().addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._roleIcon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(line())
        self._bigFive = BigFiveChart()
        self._bigFive.setTitle('')
        for bf, values in character.big_five.items():
            self._bigFive.refreshDimension(dimension_from(bf), values)
        self._bigFiveChartView = ChartView(self)
        self._bigFiveChartView.setChart(self._bigFive)

        self.layout().addWidget(self._bigFiveChartView)


class LayoutType(Enum):
    HORIZONTAL = 0
    VERTICAL = 1
    FLOW = 2


class CharacterComparisonWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._characters: Dict[Character, CharacterOverviewWidget] = {}
        hbox(self, spacing=0)

    def updateCharacter(self, character: Character, enabled: bool):
        if enabled:
            wdg = CharacterOverviewWidget(character)
            self._characters[character] = wdg
            self.layout().addWidget(wdg)
        else:
            wdg = self._characters.pop(character)
            self.layout().removeWidget(wdg)

    def updateLayout(self, layoutType: LayoutType):
        widgets = []
        for i in range(self.layout().count()):
            widgets.append(self.layout().itemAt(i).widget())

        sip.delete(self.layout())

        if layoutType == LayoutType.HORIZONTAL:
            hbox(self, spacing=0)
        elif layoutType == LayoutType.VERTICAL:
            vbox(self, spacing=0)
        elif layoutType == LayoutType.FLOW:
            flow(self, spacing=0)

        for wdg in widgets:
            self.layout().addWidget(wdg)
