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
from typing import Optional

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtWidgets import QWidget, QLabel
from overrides import overrides
from qthandy import vbox, hbox, bold

from src.main.python.plotlyst.view.widget.display import Icon


class ContainerNode(QWidget):
    selectionChanged = pyqtSignal(bool)

    def __init__(self, title: str, icon: Optional[QIcon] = None, parent=None):
        super(ContainerNode, self).__init__(parent)
        vbox(self)
        self._selected: bool = False

        self._wdgTitle = QWidget(self)
        hbox(self._wdgTitle, 0, 2)

        self._lblTitle = QLabel(title)
        self._icon = Icon(self._wdgTitle)
        if icon:
            self._icon.setIcon(icon)
        else:
            self._icon.setHidden(True)

        self._wdgTitle.layout().addWidget(self._icon)
        self._wdgTitle.layout().addWidget(self._lblTitle)

        self.layout().addWidget(self._wdgTitle)

        self._wdgTitle.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            qtanim.glow(self._wdgTitle, radius=4, duration=100, color=Qt.GlobalColor.lightGray)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self._toggleSelection(not self._selected)
            self.selectionChanged.emit(self._selected)
        return super(ContainerNode, self).eventFilter(watched, event)

    def select(self):
        self._toggleSelection(True)

    def deselect(self):
        self._toggleSelection(False)

    def _toggleSelection(self, selected: bool):
        self._selected = selected
        bold(self._lblTitle, self._selected)
        self._reStyle()

    def _reStyle(self):
        if self._selected:
            self._wdgTitle.setStyleSheet('''
                       QWidget {
                           background-color: #D8D5D5;
                       }
                   ''')
        else:
            self._wdgTitle.setStyleSheet('')


class TreeView(QScrollArea):
    def __init__(self, parent=None):
        super(TreeView, self).__init__(parent)
