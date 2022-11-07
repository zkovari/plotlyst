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
import qtanim
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QFrame, QSizePolicy, QLabel, QToolButton, QGraphicsDropShadowEffect, QPushButton
from qthandy import vbox, hbox, transparent, vspacer, margins, spacer, bold, retain_when_hidden
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter

from src.main.python.plotlyst.core.domain import TaskStatus, Task, Novel
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.common import ButtonPressResizeEventFilter, pointy
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import CollapseButton

TASK_WIDGET_MAX_WIDTH = 350


def shadow(wdg: QWidget):
    effect = QGraphicsDropShadowEffect(wdg)
    effect.setBlurRadius(0)
    effect.setOffset(2, 2)
    effect.setColor(Qt.GlobalColor.lightGray)
    wdg.setGraphicsEffect(effect)


class TaskWidget(QFrame):
    def __init__(self, task: Task, parent=None):
        super(TaskWidget, self).__init__(parent)
        self._task = task
        self.setStyleSheet('TaskWidget {background: white; border: 1px solid white; border-radius: 6px;}')
        shadow(self)

        vbox(self)
        self._lblTitle = QLabel(self._task.title, self)
        self.layout().addWidget(self._lblTitle, alignment=Qt.AlignmentFlag.AlignTop)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMinimumHeight(75)


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
        bold(self._title)
        self._btnCollapse = CollapseButton(Qt.Edge.BottomEdge, Qt.Edge.LeftEdge, self)
        self.installEventFilter(VisibilityToggleEventFilter(self._btnCollapse, self))
        shadow(self)

        self._btnAdd = QToolButton()
        self._btnAdd.setIcon(IconRegistry.plus_icon('grey'))
        transparent(self._btnAdd)
        retain_when_hidden(self._btnAdd)
        self._btnAdd.setStyleSheet('''
            QToolButton {
                border-radius: 12px;
                border: 1px hidden lightgrey;
                padding: 2px;
            }

            QToolButton:hover {
                background: lightgrey;
            }
        ''')
        pointy(self._btnAdd)
        self._btnAdd.installEventFilter(ButtonPressResizeEventFilter(self._btnAdd))
        self.installEventFilter(VisibilityToggleEventFilter(self._btnAdd, self))

        self.layout().addWidget(self._title)
        self.layout().addWidget(self._btnCollapse)
        self.layout().addWidget(self._btnAdd)

        self._btnCollapse.clicked.connect(self.collapseToggled.emit)
        self._btnAdd.clicked.connect(self.addTask.emit)


class StatusColumnWidget(QWidget):
    def __init__(self, novel: Novel, status: TaskStatus, parent=None):
        super(StatusColumnWidget, self).__init__(parent)
        self._novel = novel
        self._status = status
        vbox(self, 3, 4)
        self._header = StatusHeader(self._status)
        self._container = QWidget(self)
        spacing = 6 if app_env.is_mac() else 12
        vbox(self._container, margin=5, spacing=spacing)
        self.setMaximumWidth(TASK_WIDGET_MAX_WIDTH)
        self.layout().addWidget(self._header)
        self.layout().addWidget(self._container)
        self.layout().addWidget(vspacer())

        self._btnAdd = QPushButton('New Task', self)
        self._btnAdd.setIcon(IconRegistry.plus_icon('grey'))
        transparent(self._btnAdd)
        pointy(self._btnAdd)
        self._btnAdd.installEventFilter(ButtonPressResizeEventFilter(self._btnAdd))
        self._btnAdd.installEventFilter(OpacityEventFilter(self._btnAdd))

        self._container.layout().addWidget(self._btnAdd, alignment=Qt.AlignmentFlag.AlignLeft)

        self.installEventFilter(VisibilityToggleEventFilter(self._btnAdd, self))

        self._btnAdd.clicked.connect(self._addNewTask)
        self._header.addTask.connect(self._addNewTask)

    def addTask(self, task: Task):
        wdg = TaskWidget(task, self)
        self._container.layout().insertWidget(self._container.layout().count() - 1, wdg,
                                              alignment=Qt.AlignmentFlag.AlignTop)
        qtanim.fade_in(wdg, 150)

    def _addNewTask(self):
        task = Task('New task', self._status.id)
        self._novel.board.tasks.append(task)
        self.addTask(task)


class BoardWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super(BoardWidget, self).__init__(parent)
        self._novel = novel

        hbox(self, spacing=20)
        for status in self._novel.board.statuses:
            self.layout().addWidget(StatusColumnWidget(novel, status))
        _spacer = spacer()
        _spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.layout().addWidget(_spacer)
        margins(self, left=20)
