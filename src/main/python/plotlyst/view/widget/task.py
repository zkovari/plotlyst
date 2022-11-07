"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QFrame, QSizePolicy, QLabel, QToolButton
from qthandy import vbox, hbox, incr_font, bold, transparent
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter

from src.main.python.plotlyst.core.domain import TaskStatus, Task, Novel
from src.main.python.plotlyst.view.common import ButtonPressResizeEventFilter, pointy
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import CollapseButton

TASK_WIDGET_MAX_WIDTH = 450


class TaskWidget(QWidget):
    def __init__(self, task: Task, parent=None):
        super(TaskWidget, self).__init__(parent)
        self._task = task


class StatusHeader(QFrame):
    collapseToggled = pyqtSignal(bool)
    addTask = pyqtSignal()

    def __init__(self, status: TaskStatus, parent=None):
        super(StatusHeader, self).__init__(parent)
        self._status = status
        self.setStyleSheet(f'''StatusHeader {{
                background: white;
                border-bottom: 3px solid {self._status.color_hexa};
            }}''')
        hbox(self, margin=8)
        self._title = QLabel(self._status.text.upper(), self)
        incr_font(self._title)
        bold(self._title)
        self._btnCollapse = CollapseButton(Qt.Edge.BottomEdge, Qt.Edge.LeftEdge, self)
        self._btnCollapse.installEventFilter(OpacityEventFilter(self._btnCollapse))
        self.installEventFilter(VisibilityToggleEventFilter(self._btnCollapse, self))

        self._btnAdd = QToolButton(self)
        self._btnAdd.setIcon(IconRegistry.plus_icon('grey'))
        self._btnAdd.installEventFilter(OpacityEventFilter(self._btnCollapse))
        transparent(self._btnAdd)
        pointy(self._btnAdd)
        self._btnAdd.installEventFilter(ButtonPressResizeEventFilter(self._btnAdd))
        self.installEventFilter(VisibilityToggleEventFilter(self._btnAdd, self))

        self.layout().addWidget(self._title)
        self.layout().addWidget(self._btnCollapse)
        self.layout().addWidget(self._btnAdd)

        self._btnCollapse.clicked.connect(self.collapseToggled.emit)
        self._btnAdd.clicked.connect(self.addTask.emit)


class StatusColumnWidget(QWidget):
    def __init__(self, status: TaskStatus, parent=None):
        super(StatusColumnWidget, self).__init__(parent)
        self._status = status
        vbox(self, 3, 4)
        self._header = StatusHeader(self._status)
        self._container = QWidget()
        vbox(self._container)
        self._container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMaximumWidth(TASK_WIDGET_MAX_WIDTH)
        self.layout().addWidget(self._header)
        self.layout().addWidget(self._container)


class BoardWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super(BoardWidget, self).__init__(parent)
        self._novel = novel

        hbox(self)
        for status in self._novel.board.statuses:
            self.layout().addWidget(StatusColumnWidget(status))
