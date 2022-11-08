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
from typing import List

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QFrame, QSizePolicy, QLabel, QToolButton, QPushButton, \
    QLineEdit
from qthandy import vbox, hbox, transparent, vspacer, margins, spacer, bold, retain_when_hidden, incr_font
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter

from src.main.python.plotlyst.core.domain import TaskStatus, Task, Novel
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.common import ButtonPressResizeEventFilter, pointy, shadow
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import CollapseButton

TASK_WIDGET_MAX_WIDTH = 350


class TaskWidget(QFrame):
    def __init__(self, task: Task, parent=None):
        super(TaskWidget, self).__init__(parent)
        self._task = task
        self.setStyleSheet('TaskWidget {background: white; border: 1px solid lightGrey; border-radius: 6px;}')

        vbox(self, margin=5)
        self._lineTitle = QLineEdit(self)
        self._lineTitle.setPlaceholderText('New task')
        self._lineTitle.setText(task.title)
        self._lineTitle.setFrame(False)
        font = QFont('Arial')
        font.setWeight(QFont.Weight.Medium)
        self._lineTitle.setFont(font)
        incr_font(self._lineTitle)
        self.layout().addWidget(self._lineTitle, alignment=Qt.AlignmentFlag.AlignTop)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMinimumHeight(75)
        shadow(self, 3)

        self._lineTitle.textEdited.connect(self._titleEdited)

    def activate(self):
        anim = qtanim.fade_in(self, 150)
        anim.finished.connect(self._activated)

    def _titleEdited(self, text: str):
        self._task.title = text

    def _activated(self):
        self._lineTitle.setFocus()
        shadow(self, 3)


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
        vbox(self, 1, 20)
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

    def status(self) -> TaskStatus:
        return self._status

    def addTask(self, task: Task, edit: bool = False):
        wdg = TaskWidget(task, self)
        self._container.layout().insertWidget(self._container.layout().count() - 1, wdg,
                                              alignment=Qt.AlignmentFlag.AlignTop)

        if edit:
            wdg.activate()

    def _addNewTask(self):
        task = Task('', self._status.id)
        self._novel.board.tasks.append(task)
        self.addTask(task, edit=True)


class BoardWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super(BoardWidget, self).__init__(parent)
        self._novel = novel

        hbox(self, spacing=20)
        self._statusHeaders: List[StatusColumnWidget] = []
        for status in self._novel.board.statuses:
            header = StatusColumnWidget(novel, status)
            self.layout().addWidget(header)
            self._statusHeaders.append(header)
        _spacer = spacer()
        _spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.layout().addWidget(_spacer)
        margins(self, left=20)

    def addNewTask(self):
        if self._statusHeaders:
            header = self._statusHeaders[0]
            task = Task('', header.status().id)
            header.addTask(task, edit=True)
