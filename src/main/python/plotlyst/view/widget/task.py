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

from PyQt6.QtWidgets import QWidget, QLabel
from qthandy import vbox, hbox

from src.main.python.plotlyst.core.domain import TaskStatus, Task, Novel


class TaskWidget(QWidget):
    def __init__(self, task: Task, parent=None):
        super(TaskWidget, self).__init__(parent)
        self._task = task


class StatusColumnWidget(QWidget):
    def __init__(self, status: TaskStatus, parent=None):
        super(StatusColumnWidget, self).__init__(parent)
        self._status = status
        vbox(self)
        self._lblStatus = QLabel(self._status.text)
        self.layout().addWidget(self._lblStatus)


class BoardWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super(BoardWidget, self).__init__(parent)
        self._novel = novel
        hbox(self)
        for status in self._novel.board.statuses:
            self.layout().addWidget(StatusColumnWidget(status))
