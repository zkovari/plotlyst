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
from functools import partial
from typing import Dict, Set, Optional

import qtanim
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QObject, QEvent
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QFrame, QSizePolicy, QLabel, QToolButton, QPushButton, \
    QLineEdit, QMenu
from overrides import overrides
from qthandy import vbox, hbox, transparent, vspacer, margins, spacer, bold, retain_when_hidden, incr_font, \
    btn_popup_menu, gc, vline
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter, DragEventFilter, DropEventFilter

from src.main.python.plotlyst.core.domain import TaskStatus, Task, Novel, Character
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import Event, emit_event, EventListener
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import CharacterDeletedEvent, TaskChanged, TaskDeleted, TaskChangedToWip, \
    TaskChangedFromWip
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import ButtonPressResizeEventFilter, pointy, shadow
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.button import CollapseButton
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorButton
from src.main.python.plotlyst.view.widget.display import Icon

TASK_WIDGET_MAX_WIDTH = 350

TASK_MIME_TYPE: str = 'application/task'


class TaskWidget(QFrame):
    removalRequested = pyqtSignal(object)
    changed = pyqtSignal()

    def __init__(self, task: Task, parent=None):
        super(TaskWidget, self).__init__(parent)
        self._task: Task = task
        self.setStyleSheet('TaskWidget {background: white; border: 1px solid lightGrey; border-radius: 6px;}')

        vbox(self, margin=5)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMinimumHeight(75)
        shadow(self, 3)

        self._lineTitle = QLineEdit(self)
        self._lineTitle.setPlaceholderText('New task')
        self._lineTitle.setText(task.title)
        self._lineTitle.setFrame(False)
        font = QFont('Arial')
        font.setWeight(QFont.Weight.Medium)
        self._lineTitle.setFont(font)
        incr_font(self._lineTitle)

        self._charSelector = CharacterSelectorButton(app_env.novel, self, opacityEffectEnabled=False, iconSize=24)
        self._charSelector.setToolTip('Link character')
        if self._task.character_id:
            self._charSelector.setCharacter(self._task.character(app_env.novel))
        else:
            self._charSelector.setHidden(True)
        retain_when_hidden(self._charSelector)
        self._charSelector.characterSelected.connect(self._linkCharacter)
        top_wdg = group(self._lineTitle, self._charSelector, margin=0, spacing=1)
        self.layout().addWidget(top_wdg, alignment=Qt.AlignmentFlag.AlignTop)

        self._wdgBottom = QWidget()
        retain_when_hidden(self._wdgBottom)
        vbox(self._wdgBottom)
        self._btnMenu = QToolButton(self._wdgBottom)
        self._btnMenu.setIcon(IconRegistry.dots_icon('grey'))
        self._btnMenu.setStyleSheet('''
                    QToolButton {
                        border-radius: 12px;
                        border: 1px hidden lightgrey;
                        padding: 2px;
                    }
                    QToolButton::menu-indicator {
                        width:0px;
                    }

                    QToolButton:hover {
                        background: lightgrey;
                    }
                ''')
        pointy(self._btnMenu)
        menu = QMenu(self._btnMenu)
        menu.addAction(IconRegistry.edit_icon(), 'Rename', self._lineTitle.setFocus)
        menu.addSeparator()
        menu.addAction(IconRegistry.trash_can_icon(), 'Delete', lambda: self.removalRequested.emit(self))
        btn_popup_menu(self._btnMenu, menu)
        self._wdgBottom.layout().addWidget(self._btnMenu, alignment=Qt.AlignmentFlag.AlignRight)
        self.layout().addWidget(self._wdgBottom, alignment=Qt.AlignmentFlag.AlignBottom)

        self.installEventFilter(VisibilityToggleEventFilter(self._btnMenu, self))
        self.installEventFilter(self)
        self._lineTitle.textEdited.connect(self._titleEdited)
        self._lineTitle.editingFinished.connect(self._titleEditingFinished)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            if not self._task.character_id:
                self._charSelector.setVisible(True)
        elif event.type() == QEvent.Type.Leave:
            if not self._task.character_id and not self._charSelector.menu().isVisible():
                self._charSelector.setHidden(True)

        return super(TaskWidget, self).eventFilter(watched, event)

    def task(self) -> Task:
        return self._task

    def activate(self):
        anim = qtanim.fade_in(self, 150)
        anim.finished.connect(self._activated)

    def _titleEdited(self, text: str):
        self._task.title = text
        self.changed.emit()

    def _titleEditingFinished(self):
        if not self._task.title:
            self.removalRequested.emit(self)

    def _activated(self):
        self._lineTitle.setFocus()
        shadow(self, 3)

    def _linkCharacter(self, character: Character):
        self._task.set_character(character)
        self._charSelector.setVisible(True)
        self.changed.emit()

    def resetCharacter(self):
        self._task.reset_character()
        self._charSelector.clear()


class _StatusHeader(QFrame):
    collapseToggled = pyqtSignal(bool)
    addTask = pyqtSignal()

    def __init__(self, status: TaskStatus, parent=None):
        super(_StatusHeader, self).__init__(parent)
        self._status = status
        self.setStyleSheet(f'''_StatusHeader {{
                background: white;
                border-bottom: 3px solid {self._status.color_hexa};
            }}''')
        hbox(self, margin=8)

        self._title = QLabel(self)
        bold(self._title)
        self.updateTitle()
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
        self.layout().addWidget(spacer())
        self.layout().addWidget(self._btnAdd)

        self._btnCollapse.clicked.connect(self.collapseToggled.emit)
        self._btnAdd.clicked.connect(self.addTask.emit)

    def toggled(self) -> bool:
        return self._btnCollapse.isChecked()

    def updateTitle(self, childrenCount: int = 0):
        suffix = f'({childrenCount})' if childrenCount else ''
        self._title.setText(f'{self._status.text.upper()} {suffix}')


class StatusColumnWidget(QFrame):
    taskChanged = pyqtSignal(Task)
    taskDeleted = pyqtSignal(Task)

    def __init__(self, novel: Novel, status: TaskStatus, parent=None):
        super(StatusColumnWidget, self).__init__(parent)
        self._novel = novel
        self._status = status
        vbox(self, 1, 20)
        self._header = _StatusHeader(self._status)
        self._header.collapseToggled.connect(self._collapseToggled)
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
        self.setAcceptDrops(True)
        self.installEventFilter(
            DropEventFilter(self, [TASK_MIME_TYPE], enteredSlot=self._dragEntered, leftSlot=self._dragLeft,
                            droppedSlot=self._dropped))

        self._btnAdd.clicked.connect(self._addNewTask)
        self._header.addTask.connect(self._addNewTask)

        event_dispatcher.register(self, CharacterDeletedEvent)

    def event_received(self, event: Event):
        if isinstance(event, CharacterDeletedEvent):
            for i in range(self._container.layout().count() - 1):
                item = self._container.layout().itemAt(i)
                if item.widget():
                    taskWdg: TaskWidget = item.widget()
                    if taskWdg.task().character_id == event.character.id:
                        taskWdg.resetCharacter()
                        self.taskChanged.emit(taskWdg.task())

    def status(self) -> TaskStatus:
        return self._status

    def addTask(self, task: Task, edit: bool = False) -> TaskWidget:
        wdg = TaskWidget(task, self)
        self._container.layout().insertWidget(self._container.layout().count() - 1, wdg,
                                              alignment=Qt.AlignmentFlag.AlignTop)
        wdg.installEventFilter(
            DragEventFilter(self, mimeType=TASK_MIME_TYPE, dataFunc=self._grabbedTaskData,
                            startedSlot=lambda: wdg.setDisabled(True),
                            finishedSlot=lambda: self._dragFinished(wdg)))
        wdg.removalRequested.connect(self._deleteTask)
        wdg.changed.connect(partial(self.taskChanged.emit, task))
        if edit:
            wdg.activate()

        if self._status.wip:
            emit_event(TaskChangedToWip(self, task))

        self._header.updateTitle(self._container.layout().count() - 1)
        return wdg

    def _addNewTask(self):
        task = Task('', self._status.id)
        self._novel.board.tasks.append(task)
        self.addTask(task, edit=True)

    def _deleteTask(self, taskWidget: TaskWidget):
        task = taskWidget.task()
        self._novel.board.tasks.remove(task)
        self.__removeTaskWidget(taskWidget)
        self.taskDeleted.emit(task)

    def _collapseToggled(self, toggled: bool):
        for i in range(self._container.layout().count()):
            item = self._container.layout().itemAt(i)
            if item.widget() and isinstance(item.widget(), TaskWidget):
                item.widget().setHidden(toggled)

    def _grabbedTaskData(self, widget: TaskWidget):
        return widget.task()

    def _dragEntered(self, _: QMimeData):
        self.setStyleSheet(f'StatusColumnWidget {{border: 2px dashed {self._status.color_hexa};}}')

    def _dragLeft(self):
        self.setStyleSheet('')

    def _dragFinished(self, taskWidget: TaskWidget):
        if taskWidget.task().status_ref == self._status.id:
            taskWidget.setEnabled(True)
        else:
            if self._status.wip:
                emit_event(TaskChangedFromWip(self, taskWidget.task()))
            self.__removeTaskWidget(taskWidget)

    def _dropped(self, mimeData: QMimeData):
        self.setStyleSheet('')
        task: Task = mimeData.reference()
        if task.status_ref == self._status.id:
            return
        task.status_ref = self._status.id
        if self._status.resolves:
            task.update_resolved_date()

        self.taskChanged.emit(task)
        wdg = self.addTask(task)
        wdg.setHidden(self._header.toggled())

    def __removeTaskWidget(self, taskWidget):
        taskWidget.setHidden(True)
        self._container.layout().removeWidget(taskWidget)
        gc(taskWidget)
        self._header.updateTitle(self._container.layout().count() - 1)


class BoardWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super(BoardWidget, self).__init__(parent)
        self._novel = novel

        hbox(self, spacing=20)
        self._statusColumns: Dict[str, StatusColumnWidget] = {}
        for status in self._novel.board.statuses:
            column = StatusColumnWidget(novel, status)
            column.taskChanged.connect(self._taskChanged)
            column.taskDeleted.connect(self._taskDeleted)
            self.layout().addWidget(column)
            self._statusColumns[str(status.id)] = column

        for task in novel.board.tasks:
            column = self._statusColumns.get(str(task.status_ref))
            if column is None:
                column = self._firstStatusColumn()
            column.addTask(task)

        _spacer = spacer()
        _spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.layout().addWidget(_spacer)
        margins(self, left=20)

        self.repo = RepositoryPersistenceManager.instance()

    def addNewTask(self):
        if self._statusColumns:
            column = self._firstStatusColumn()
            task = Task('', column.status().id)
            self._novel.board.tasks.append(task)
            column.addTask(task, edit=True)

    def _firstStatusColumn(self) -> StatusColumnWidget:
        return self._statusColumns[str(self._novel.board.statuses[0].id)]

    def _taskChanged(self, task: Task):
        self._saveBoard()
        emit_event(TaskChanged(self, task))

    def _taskDeleted(self, task: Task):
        self._saveBoard()
        emit_event(TaskDeleted(self, task))

    def _saveBoard(self):
        self.repo.update_novel(self._novel)


class TasksQuickAccessWidget(QWidget, EventListener):
    def __init__(self, parent=None):
        super(TasksQuickAccessWidget, self).__init__(parent)
        hbox(self)
        self._title = QLabel('Test')
        self._icon = Icon()
        self._icon.setIcon(IconRegistry.board_icon())
        self._icon.setToolTip('Pinned in-progress task')
        self._btnSelector = QToolButton()
        self._btnSelector.setProperty('transparent', True)
        pointy(self._btnSelector)
        self._btnSelector.setToolTip('Select an other in-progress task')
        self._btnSelector.setIcon(IconRegistry.from_name('fa5s.tasks'))
        self._menu = QMenu(self._btnSelector)
        btn_popup_menu(self._btnSelector, self._menu)
        self._menu.aboutToShow.connect(self._fillSelectorPopup)

        self.layout().addWidget(self._icon)
        self.layout().addWidget(vline())
        self.layout().addWidget(self._btnSelector)
        self.layout().addWidget(self._title)

        self._tasks: Set[Task] = set()
        self._currentTask: Optional[Task] = None
        self._updateCurrentTask()

        event_dispatcher.register(self, TaskChanged)
        event_dispatcher.register(self, TaskDeleted)
        event_dispatcher.register(self, TaskChangedToWip)
        event_dispatcher.register(self, TaskChangedFromWip)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, TaskChangedToWip):
            self.addTask(event.task)
        elif isinstance(event, TaskChangedFromWip):
            self.removeTask(event.task)
        elif isinstance(event, TaskChanged):
            if event.task not in self._tasks:
                return
            if event.task == self._currentTask:
                self._updateCurrentTask()

        elif isinstance(event, TaskDeleted):
            self.removeTask(event.task)

    def addTask(self, task: Task):
        self._tasks.add(task)
        if self._currentTask is None:
            # self._currentTask = task
            self._updateCurrentTask(task)

        self._toggleSelector()

    def removeTask(self, task: Task):
        if task in self._tasks:
            self._tasks.remove(task)
        if self._currentTask == task:
            # self._currentTask = next(iter(self._tasks), None)
            self._updateCurrentTask()

        self._toggleSelector()

    def reset(self):
        self._currentTask = None
        self._tasks.clear()
        self._updateCurrentTask()

    def _updateCurrentTask(self, task: Optional[Task] = None):
        if task:
            self._currentTask = task
        else:
            self._currentTask = next(iter(self._tasks), None)

        if self._currentTask:
            self._title.setText(self._currentTask.title)
        else:
            self._title.clear()

        self.setHidden(self._currentTask is None)

    def _toggleSelector(self):
        self._btnSelector.setVisible(len(self._tasks) > 1)

    def _fillSelectorPopup(self):
        self._menu.clear()
        for task in self._tasks:
            self._menu.addAction(task.title, partial(self._updateCurrentTask, task))
