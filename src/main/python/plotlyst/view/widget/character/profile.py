"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
from typing import Optional, List, Dict

from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import QWidget
from overrides import overrides
from qthandy import vbox, clear_layout, hbox, bold, underline, spacer, vspacer, margins

from plotlyst.core.domain import Character, CharacterProfileSectionReference
from plotlyst.view.common import tool_btn, label
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.button import CollapseButton
from plotlyst.view.widget.progress import CircularProgressBar


class ProfileFieldWidget(QWidget):
    valueFilled = pyqtSignal(float)
    valueReset = pyqtSignal()


class ProfileSectionWidget(ProfileFieldWidget):
    headerEnabledChanged = pyqtSignal(bool)

    def __init__(self, section: CharacterProfileSectionReference, parent=None):
        super().__init__(parent)
        self.section = section
        vbox(self)
        self.btnHeader = CollapseButton(Qt.Edge.BottomEdge, Qt.Edge.RightEdge)
        self.btnHeader.setIconSize(QSize(16, 16))
        bold(self.btnHeader)
        underline(self.btnHeader)
        self.btnHeader.setText(section.type.name)
        self.btnHeader.setToolTip(section.type.name)

        self.wdgHeader = QWidget()
        hbox(self.wdgHeader, 1, 0)
        self.wdgHeader.layout().addWidget(self.btnHeader)
        self.progress = CircularProgressBar()
        self.wdgHeader.layout().addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.wdgHeader.layout().addWidget(spacer())

        self.wdgContainer = QWidget()
        vbox(self.wdgContainer, 0)
        margins(self.wdgContainer, left=20)

        self.layout().addWidget(self.wdgHeader)
        self.layout().addWidget(self.wdgContainer)

        self.children: List[ProfileFieldWidget] = []
        self.progressStatuses: Dict[ProfileFieldWidget, float] = {}

        self.btnHeader.toggled.connect(self._toggleCollapse)

    def attachWidget(self, widget: ProfileFieldWidget):
        self.children.append(widget)
        self.wdgContainer.layout().addWidget(widget)
        # if not widget.field.type.is_display():
        self.progressStatuses[widget] = False
        # widget.valueFilled.connect(partial(self._valueFilled, widget))
        # widget.valueReset.connect(partial(self._valueReset, widget))

    def updateProgress(self):
        self.progress.setMaxValue(len(self.progressStatuses.keys()))
        self.progress.update()

    def collapse(self, collapsed: bool):
        self.btnHeader.setChecked(collapsed)

    def _toggleCollapse(self, checked: bool):
        self.wdgContainer.setHidden(checked)

    def _valueFilled(self, widget: ProfileFieldWidget, value: float):
        if self.progressStatuses[widget] == value:
            return

        self.progressStatuses[widget] = value
        self.progress.setValue(sum(self.progressStatuses.values()))

    def _valueReset(self, widget: ProfileFieldWidget):
        if not self.progressStatuses[widget]:
            return

        self.progressStatuses[widget] = 0
        self.progress.setValue(sum(self.progressStatuses.values()))


class CharacterProfileEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._character: Optional[Character] = None
        self.btnCustomize = tool_btn(IconRegistry.preferences_icon(), tooltip='Customize character profile', base=True,
                                     parent=self)

        vbox(self)

    def setCharacter(self, character: Character):
        self._character = character
        self.refresh()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.btnCustomize.setGeometry(event.size().width() - 30, 2, 25, 25)

    def refresh(self):
        clear_layout(self)

        for section in self._character.profile:
            wdg = ProfileSectionWidget(section)
            self.layout().addWidget(wdg)
            for field in section.fields:
                fieldWdg = label(field.type.name)
                wdg.attachWidget(fieldWdg)

        self.layout().addWidget(vspacer())
