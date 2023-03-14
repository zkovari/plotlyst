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
import sys
from functools import partial
from typing import Dict

import emoji
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QPaintEvent, QPainter, QPen, QColor, QPainterPath, QShowEvent
from PyQt6.QtWidgets import QWidget, QMainWindow, QApplication, QLabel, QLineEdit, QSizePolicy, QMenu, \
    QPushButton
from overrides import overrides
from qthandy import vbox, vspacer, hbox, spacer, transparent, margins, line, retain_when_hidden, btn_popup_menu, \
    decr_font, curved_flow, gc
from qthandy.filter import VisibilityToggleEventFilter

from src.main.python.plotlyst.core.domain import Character, CharacterGoal, Novel, CharacterPlan, Goal
from src.main.python.plotlyst.view.common import emoji_font, ButtonPressResizeEventFilter, pointy, action, wrap
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.button import DotsMenuButton
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit
from src.main.python.plotlyst.view.widget.utility import IconSelectorButton


class _AddObjectiveButton(QPushButton):
    addNew = pyqtSignal()
    selectExisting = pyqtSignal()

    def __init__(self, parent=None):
        super(_AddObjectiveButton, self).__init__(parent)
        self.setIcon(IconRegistry.plus_icon('grey'))
        self.setToolTip('Add new objective')
        transparent(self)
        self.setStyleSheet(f'{self.styleSheet()}\nQPushButton{{ color: grey;}}')
        pointy(self)
        retain_when_hidden(self)
        menu = QMenu(self)
        menu.addAction(action('Add new objective', IconRegistry.goal_icon(), self.addNew.emit, parent=menu))
        menu.addSeparator()
        menu.addAction(
            action('Select objective from a character', IconRegistry.character_icon(), self.selectExisting.emit,
                   parent=menu))
        btn_popup_menu(self, menu)

        self.installEventFilter(ButtonPressResizeEventFilter(self))


class CharacterSubtaskWidget(QWidget):
    delete = pyqtSignal()

    def __init__(self, novel: Novel, goalRef: CharacterGoal, parent=None):
        super(CharacterSubtaskWidget, self).__init__(parent)
        self._novel = novel
        self._goalRef = goalRef
        self._goal = goalRef.goal(self._novel)

        self.iconSelector = IconSelectorButton()
        self.iconSelector.selectIcon('mdi.target', 'darkBlue')
        self.iconSelector.setIconSize(QSize(16, 16))
        self.lineText = QLineEdit()
        self.lineText.setPlaceholderText('Subtask')
        transparent(self.lineText)
        decr_font(self.lineText)
        self.lineText.setText(self._goal.text)

        menu = QMenu()
        menu.addAction(IconRegistry.trash_can_icon(), 'Delete', self.delete.emit)
        self.btnMenu = DotsMenuButton(menu)

        hbox(self)
        self.layout().addWidget(self.iconSelector)
        self.layout().addWidget(self.lineText)
        self.layout().addWidget(self.btnMenu)

        self.installEventFilter(VisibilityToggleEventFilter(self.btnMenu, self))

    def subtask(self) -> CharacterGoal:
        return self._goalRef


class CharacterGoalWidget(QWidget):
    addNew = pyqtSignal()
    delete = pyqtSignal()
    subtasksChanged = pyqtSignal()
    selectExisting = pyqtSignal()

    def __init__(self, novel: Novel, goalRef: CharacterGoal, parent=None):
        super(CharacterGoalWidget, self).__init__(parent)
        self._novel = novel
        self._goalRef = goalRef
        self._goal = goalRef.goal(self._novel)

        vbox(self, 0)
        self._wdgCenter = QWidget()
        hbox(self._wdgCenter, 0, 0)
        self.iconSelector = IconSelectorButton()
        self.iconSelector.selectIcon('mdi.target', 'darkBlue')
        self.iconSelector.iconSelected.connect(self._iconSelected)
        self.lineText = QLineEdit()
        self.lineText.setMinimumWidth(150)
        self.lineText.setPlaceholderText('Objective')
        self.lineText.setText(self._goal.text)
        self.lineText.setToolTip(self._goal.text)
        self.lineText.textEdited.connect(self._textEdited)
        transparent(self.lineText)
        self.hLine = line()
        retain_when_hidden(self.hLine)
        self.hLine.setHidden(True)

        self.btnAdd = _AddObjectiveButton()
        self.btnAddBefore = _AddObjectiveButton()
        menu = QMenu()
        menu.addAction(IconRegistry.trash_can_icon(), 'Delete', self.delete.emit)
        self.btnMenu = DotsMenuButton(menu)

        self._wdgCenter.layout().addWidget(self.btnAddBefore)
        self._wdgCenter.layout().addWidget(self.iconSelector)
        self._wdgCenter.layout().addWidget(group(
            group(self.lineText, self.btnMenu, self.btnAdd, margin=0, spacing=0),
            self.hLine, vertical=False))

        self._wdgBottom = QWidget()
        vbox(self._wdgBottom, 0, 0)
        self._btnAddSubtask = _AddObjectiveButton()
        self._btnAddSubtask.setText('Add subtask')
        self._btnAddSubtask.addNew.connect(self._addNewSubtask)
        decr_font(self._btnAddSubtask)
        self._wdgBottom.layout().addWidget(wrap(self._btnAddSubtask, margin_left=30),
                                           alignment=Qt.AlignmentFlag.AlignLeft)

        for child in self._goalRef.children:
            self._addSubtaskWidget(child)

        self._wdgCenter.installEventFilter(VisibilityToggleEventFilter(self.btnAdd, self))
        self._wdgCenter.installEventFilter(VisibilityToggleEventFilter(self.btnAddBefore, self))
        self._wdgCenter.installEventFilter(VisibilityToggleEventFilter(self.btnMenu, self))
        self.installEventFilter(VisibilityToggleEventFilter(self._btnAddSubtask, self))

        self.layout().addWidget(self._wdgCenter)
        self.layout().addWidget(self._wdgBottom)

    def goal(self) -> CharacterGoal:
        return self._goalRef

    def _textEdited(self, text: str):
        self.btnAdd.setHidden(True)
        self.btnAddBefore.setHidden(True)
        self._goal.text = text
        self.lineText.setToolTip(text)

        # self.repo.update_novel(self.novel)

    def _iconSelected(self, icon: str, color: QColor):
        self._goal.icon = icon
        self._goal.icon_color = color.name()
        # self.repo.update_novel(self.novel)

    def _addNewSubtask(self):
        goal = Goal('')
        self._novel.goals.append(goal)

        char_goal = CharacterGoal(goal.id)
        self._goalRef.children.append(char_goal)
        self._addSubtaskWidget(char_goal)

        self.subtasksChanged.emit()

        # self.repo.update_novel(self.novel)

    def _addSubtaskWidget(self, charGoal: CharacterGoal):
        subtaskWdg = CharacterSubtaskWidget(self._novel, charGoal)
        subtaskWdg.delete.connect(partial(self._deleteSubtask, subtaskWdg))
        margins(subtaskWdg, left=self.btnAddBefore.sizeHint().width() + self.iconSelector.sizeHint().width() / 2)
        self._wdgBottom.layout().insertWidget(self._wdgBottom.layout().count() - 1, subtaskWdg)

    def _deleteSubtask(self, wdg: CharacterSubtaskWidget):
        goal = wdg.subtask()
        self._goalRef.children.remove(goal)
        self._wdgBottom.layout().removeWidget(wdg)
        gc(wdg)

        self.subtasksChanged.emit()


class CharacterPlanBarWidget(QWidget):
    def __init__(self, novel: Novel, character: Character, plan: CharacterPlan, parent=None):
        super(CharacterPlanBarWidget, self).__init__(parent)
        self._novel = novel
        self._character = character
        self._plan = plan
        vbox(self)
        self._firstShow = True

        self._wdgHeader = QWidget()
        hbox(self._wdgHeader)
        self._lblEmoji = QLabel()
        self._lblEmoji.setFont(emoji_font())
        if self._plan.external:
            self._lblEmoji.setText(emoji.emojize(':bullseye:'))
        else:
            self._lblEmoji.setText(emoji.emojize(':smiling_face_with_hearts:'))
        self._textSummary = AutoAdjustableTextEdit()
        transparent(self._textSummary)
        self._textSummary.setPlaceholderText('Summarize this goal')
        self._wdgHeader.layout().addWidget(self._lblEmoji, alignment=Qt.AlignmentFlag.AlignTop)
        self._wdgHeader.layout().addWidget(self._textSummary, alignment=Qt.AlignmentFlag.AlignTop)
        self._wdgHeader.layout().addWidget(spacer())

        self._wdgBar = QWidget()
        self._wdgBar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        curved_flow(self._wdgBar, spacing=0)
        margins(self._wdgBar, left=20, top=10, bottom=10)
        self._goalWidgets: Dict[CharacterGoal, CharacterGoalWidget] = {}
        for goal in self._plan.goals:
            goalWdg = self._initGoalWidget(goal)
            self._wdgBar.layout().addWidget(goalWdg)

        self._btnAdd = _AddObjectiveButton()
        self._btnAdd.setText('Add new objective')
        self._btnAdd.addNew.connect(lambda: self._addNewGoalAt(0))
        self._wdgBar.layout().addWidget(wrap(self._btnAdd, margin_top=50))
        if self._plan.goals:
            self._btnAdd.setHidden(True)

        self.layout().addWidget(self._wdgHeader)
        self.layout().addWidget(self._wdgBar)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.7)

        pen = QPen()
        pen.setColor(QColor('darkBlue'))
        pen.setWidth(3)
        painter.setPen(pen)

        path = QPainterPath()

        forward = True
        y = 0
        for i, goal in enumerate(self._plan.goals):
            wdg = self._goalWidgets[goal]
            pos: QPointF = wdg.mapTo(self, wdg.hLine.pos()).toPointF()
            pos.setY(pos.y() + wdg.layout().contentsMargins().top())
            pos.setX(pos.x() + wdg.layout().contentsMargins().left())
            if i == 0:
                y = pos.y()
                path.moveTo(pos)
            else:
                if pos.y() > y:
                    if forward:
                        path.arcTo(QRectF(pos.x() + wdg.hLine.width() + wdg.iconSelector.width(), y, 60, pos.y() - y),
                                   90, -180)
                    else:
                        path.arcTo(QRectF(pos.x() - wdg.btnAddBefore.width(), y, 60, pos.y() - y), -270, 180)
                        path.lineTo(pos)
                    forward = not forward
                    y = pos.y()

            if forward:
                pos.setX(pos.x() + wdg.hLine.width() + wdg.iconSelector.width())
            path.lineTo(pos)

        painter.drawPath(path)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if self._firstShow:
            self._rearrange()
            self._firstShow = False

    def _rearrange(self):
        for i, goal in enumerate(self._plan.goals):
            wdg = self._goalWidgets[goal]
            if i == 0:
                margins(wdg, left=0, top=40)
            else:
                margins(wdg, left=10, top=40)

    def _initGoalWidget(self, goal: CharacterGoal):
        goalWdg = CharacterGoalWidget(self._novel, goal)
        goalWdg.btnAdd.addNew.connect(partial(self._addNewGoal, goalWdg))
        goalWdg.btnAddBefore.addNew.connect(partial(self._addNewGoalBefore, goalWdg))
        goalWdg.subtasksChanged.connect(self.update)
        goalWdg.delete.connect(partial(self._deleteGoal, goalWdg))
        self._goalWidgets[goal] = goalWdg
        return goalWdg

    def _addNewGoal(self, ref: CharacterGoalWidget):
        i = self._plan.goals.index(ref.goal())
        self._addNewGoalAt(i + 1)
        # goal = Goal('')
        # self._novel.goals.append(goal)
        #
        # char_goal = CharacterGoal(goal.id)
        #
        # goalWidget = self._initGoalWidget(char_goal)
        # if i == len(self._plan.goals) - 1:
        #     self._wdgBar.layout().addWidget(goalWidget)
        # else:
        #     self._wdgBar.layout().insertWidget(i + 1, goalWidget)
        #
        # self._plan.goals.insert(i + 1, char_goal)
        #
        # self._rearrange()
        # self.update()
        # self.repo.update_novel(self.novel)

    def _addNewGoalBefore(self, ref: CharacterGoalWidget):
        i = self._plan.goals.index(ref.goal())
        self._addNewGoalAt(i)

    def _addNewGoalAt(self, i: int):
        goal = Goal('')
        self._novel.goals.append(goal)

        char_goal = CharacterGoal(goal.id)

        goalWidget = self._initGoalWidget(char_goal)
        self._wdgBar.layout().insertWidget(i, goalWidget)

        self._plan.goals.insert(i, char_goal)

        self._rearrange()
        self.update()

        self._btnAdd.setHidden(True)

    def _deleteGoal(self, wdg: CharacterGoalWidget):
        goal = wdg.goal()
        self._plan.goals.remove(goal)
        self._goalWidgets.pop(goal)
        self._wdgBar.layout().removeWidget(wdg)
        gc(wdg)

        if not self._plan.goals:
            self._btnAdd.setVisible(True)


class CharacterPlansWidget(QWidget):
    def __init__(self, novel: Novel, character: Character, parent=None):
        super(CharacterPlansWidget, self).__init__(parent)
        self._novel = novel
        self._character = character
        vbox(self)

        for plan in self._character.plans:
            bar = CharacterPlanBarWidget(self._novel, self._character, plan)
            self.layout().addWidget(bar)
        self.layout().addWidget(vspacer())


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)

            self.resize(500, 500)

            novel = Novel('test')
            character = Character('Name')
            plan = CharacterPlan()
            goal = Goal('Goal 1')
            novel.goals.append(goal)
            plan.goals.append(CharacterGoal(goal_id=goal.id))
            plan.goals.append(CharacterGoal(goal_id=goal.id,
                                            children=[CharacterGoal(goal_id=goal.id),
                                                      CharacterGoal(goal_id=goal.id),
                                                      CharacterGoal(goal_id=goal.id)]))
            plan.goals.append(CharacterGoal(goal_id=goal.id))
            plan.goals.append(CharacterGoal(goal_id=goal.id))

            character.plans.append(plan)
            character.plans.append(CharacterPlan(external=False))
            self.widget = CharacterPlansWidget(novel, character)
            self.setCentralWidget(self.widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
