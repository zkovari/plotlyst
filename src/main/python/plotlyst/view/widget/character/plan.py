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
import qtanim
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QSize, QRectF, QEvent
from PyQt6.QtGui import QPaintEvent, QPainter, QPen, QColor, QPainterPath, QShowEvent, QEnterEvent, QMouseEvent
from PyQt6.QtWidgets import QWidget, QMainWindow, QApplication, QLabel, QLineEdit, QSizePolicy, QMenu, \
    QPushButton, QToolButton
from overrides import overrides
from qthandy import vbox, vspacer, hbox, spacer, transparent, margins, line, retain_when_hidden, decr_font, curved_flow, \
    gc, sp, decr_icon, translucent
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.core.domain import Character, CharacterGoal, Novel, CharacterPlan, Goal
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import emoji_font, ButtonPressResizeEventFilter, pointy, action, wrap, \
    fade_out_and_gc, MouseEventDelegate
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
        self.setIconSize(QSize(18, 18))
        self.setIcon(IconRegistry.plus_icon('grey'))
        self.setToolTip('Add new objective')
        transparent(self)
        self.setStyleSheet(f'''{self.styleSheet()}
            QPushButton{{ color: grey;}}
            QPushButton:menu-indicator {{
                width: 0;
            }}
        ''')
        self.installEventFilter(OpacityEventFilter(self, leaveOpacity=0.7))
        pointy(self)
        retain_when_hidden(self)
        menu = MenuWidget(self)
        menu.addAction(action('Add new objective', IconRegistry.goal_icon(), self.addNew.emit, parent=menu))
        menu.addSeparator()
        menu.addAction(
            action('Select objective from a character', IconRegistry.character_icon(), self.selectExisting.emit,
                   parent=menu))

        self.installEventFilter(ButtonPressResizeEventFilter(self))


class _SelectableObjectiveIcon(QToolButton):
    selected = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(_SelectableObjectiveIcon, self).__init__(parent)
        transparent(self)
        pointy(self)
        self.setCheckable(True)
        translucent(self, 0.4)
        self._iconColor: str = ''

        self.clicked.connect(self._select)

    def selectIcon(self, icon: str, icon_color: str):
        self._iconColor = icon_color
        self.setIcon(IconRegistry.from_name(icon, 'grey', color_on=icon_color))
        transparent(self)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.toggle()
        self._select()

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if self.isChecked() or not self.isEnabled():
            return
        translucent(self, 1.0)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        if self.isChecked() or not self.isEnabled():
            return
        translucent(self, 0.4)

    def _select(self):
        qtanim.glow(self, duration=75, color=QColor(self._iconColor),
                    teardown=lambda: self.selected.emit(self.isChecked()))


class _AbstractCharacterObjectiveWidget(QWidget):
    selected = pyqtSignal(bool)

    def __init__(self, novel: Novel, goalRef: CharacterGoal, parent=None, selectable: bool = False):
        super(_AbstractCharacterObjectiveWidget, self).__init__(parent)
        self._novel = novel
        self._goalRef = goalRef
        self._goal = goalRef.goal(self._novel)
        self._selectable = selectable

        if selectable:
            self.iconSelector = _SelectableObjectiveIcon()
            self.iconSelector.selected.connect(self.selected.emit)
        else:
            self.iconSelector = IconSelectorButton()
            self.iconSelector.iconSelected.connect(self._iconSelected)
        if self._goal.icon:
            self.iconSelector.selectIcon(self._goal.icon, self._goal.icon_color)
        else:
            self.iconSelector.selectIcon('mdi.target', 'darkBlue')

        self.lineText = QLineEdit()
        self.lineText.setPlaceholderText('Subtask')
        self.lineText.setReadOnly(self._selectable)
        if self._selectable:
            pointy(self.lineText)
            self.lineText.installEventFilter(MouseEventDelegate(self.lineText, self.iconSelector))
        self.lineText.textEdited.connect(self._textEdited)
        transparent(self.lineText)
        decr_font(self.lineText)
        self.lineText.setText(self._goal.text)

        self.repo = RepositoryPersistenceManager.instance()

    def _textEdited(self, text: str):
        self._goal.text = text
        self.lineText.setToolTip(text)

        self.repo.update_novel(self._novel)

    def _iconSelected(self, icon: str, color: QColor):
        self._goal.icon = icon
        self._goal.icon_color = color.name()
        self.repo.update_novel(self._novel)


class CharacterSubtaskWidget(_AbstractCharacterObjectiveWidget):
    delete = pyqtSignal()

    def __init__(self, novel: Novel, goalRef: CharacterGoal, parent=None, selectable: bool = False):
        super(CharacterSubtaskWidget, self).__init__(novel, goalRef, parent, selectable)

        self.iconSelector.setIconSize(QSize(16, 16))

        self.btnMenu = DotsMenuButton()
        menu = MenuWidget(self.btnMenu)
        menu.addAction(action('Delete', IconRegistry.trash_can_icon(), self.delete.emit))
        self.btnMenu.installEventFilter(OpacityEventFilter(self.btnMenu, leaveOpacity=0.7))

        hbox(self)
        self.layout().addWidget(self.iconSelector)
        self.layout().addWidget(self.lineText)
        self.layout().addWidget(self.btnMenu)

        if self._selectable:
            self.btnMenu.setHidden(True)
        else:
            self.installEventFilter(VisibilityToggleEventFilter(self.btnMenu, self))

    def subtask(self) -> CharacterGoal:
        return self._goalRef


class CharacterGoalWidget(_AbstractCharacterObjectiveWidget):
    subtaskSelected = pyqtSignal(CharacterSubtaskWidget, bool)
    addBefore = pyqtSignal()
    addAfter = pyqtSignal()
    delete = pyqtSignal()
    subtasksChanged = pyqtSignal()
    selectExisting = pyqtSignal()

    def __init__(self, novel: Novel, goalRef: CharacterGoal, parent=None, selectable: bool = False):
        super(CharacterGoalWidget, self).__init__(novel, goalRef, parent, selectable)

        vbox(self, 0)
        self._wdgCenter = QWidget()
        hbox(self._wdgCenter, 0, 0)
        self.iconSelector.setIconSize(QSize(28, 28))
        self.hLine = line()
        retain_when_hidden(self.hLine)
        self.hLine.setHidden(True)
        self._forward = True

        self.btnAdd = _AddObjectiveButton()
        self.btnAddBefore = _AddObjectiveButton()
        self.btnAdd.addNew.connect(self._addAfter)
        self.btnAddBefore.addNew.connect(self._addBefore)
        self.btnMenu = DotsMenuButton()
        menu = MenuWidget(self.btnMenu)
        menu.addAction(action('Delete', IconRegistry.trash_can_icon(), self.delete.emit))
        self.btnMenu.installEventFilter(OpacityEventFilter(self.btnMenu, leaveOpacity=0.7))

        self._wdgCenter.layout().addWidget(self.btnAddBefore)
        self._wdgCenter.layout().addWidget(self.iconSelector)
        self._wdgCenter.layout().addWidget(group(
            group(self.lineText, self.btnMenu, self.btnAdd, margin=0, spacing=0),
            self.hLine, vertical=False))

        self._wdgBottom = QWidget()
        vbox(self._wdgBottom, 0, 0)
        self._btnAddSubtask = _AddObjectiveButton()
        decr_icon(self._btnAddSubtask)
        if not self._goalRef.children:
            self._btnAddSubtask.setText('Add subtask')
        self._btnAddSubtask.addNew.connect(self._addNewSubtask)
        decr_font(self._btnAddSubtask)
        self._wdgBottom.layout().addWidget(wrap(self._btnAddSubtask, margin_left=30),
                                           alignment=Qt.AlignmentFlag.AlignLeft)

        for child in self._goalRef.children:
            self._addSubtaskWidget(child)

        if self._selectable:
            self.btnAdd.setHidden(True)
            self.btnAddBefore.setHidden(True)
            self.btnMenu.setHidden(True)
            self._btnAddSubtask.setHidden(True)
        else:
            self._wdgCenter.installEventFilter(VisibilityToggleEventFilter(self.btnAdd, self))
            self._wdgCenter.installEventFilter(VisibilityToggleEventFilter(self.btnAddBefore, self))
            self._wdgCenter.installEventFilter(VisibilityToggleEventFilter(self.btnMenu, self))
            self.installEventFilter(VisibilityToggleEventFilter(self._btnAddSubtask, self))

        self.layout().addWidget(self._wdgCenter)
        self.layout().addWidget(self._wdgBottom)

    def goal(self) -> CharacterGoal:
        return self._goalRef

    def setForward(self, forward: bool):
        self._forward = forward

    @overrides
    def _textEdited(self, text: str):
        super(CharacterGoalWidget, self)._textEdited(text)
        self.btnAdd.setHidden(True)
        self.btnAddBefore.setHidden(True)

    def _addBefore(self):
        if self._forward:
            self.addBefore.emit()
        else:
            self.addAfter.emit()

    def _addAfter(self):
        if self._forward:
            self.addAfter.emit()
        else:
            self.addBefore.emit()

    def _addNewSubtask(self):
        goal = Goal('')
        self._novel.goals.append(goal)

        char_goal = CharacterGoal(goal.id)
        self._goalRef.children.append(char_goal)
        self._addSubtaskWidget(char_goal)

        self.subtasksChanged.emit()

        self.repo.update_novel(self._novel)

    def _addSubtaskWidget(self, charGoal: CharacterGoal):
        subtaskWdg = CharacterSubtaskWidget(self._novel, charGoal, selectable=self._selectable)
        subtaskWdg.delete.connect(partial(self._deleteSubtask, subtaskWdg))
        subtaskWdg.selected.connect(partial(self.subtaskSelected.emit, subtaskWdg))
        margins(subtaskWdg, left=self.btnAddBefore.sizeHint().width() + self.iconSelector.sizeHint().width() / 2)
        self._wdgBottom.layout().insertWidget(self._wdgBottom.layout().count() - 1, subtaskWdg)
        self._btnAddSubtask.setText('')
        subtaskWdg.lineText.setFocus()

    def _deleteSubtask(self, wdg: CharacterSubtaskWidget):
        goal = wdg.subtask()
        self._goalRef.children.remove(goal)
        self._wdgBottom.layout().removeWidget(wdg)
        gc(wdg)

        self.subtasksChanged.emit()
        if not self._goalRef.children:
            self._btnAddSubtask.setText('Add subtask')


class CharacterPlanBarWidget(QWidget):
    removed = pyqtSignal()
    goalSelected = pyqtSignal(CharacterGoalWidget, bool)
    subtaskSelected = pyqtSignal(CharacterGoalWidget, bool)

    def __init__(self, novel: Novel, character: Character, plan: CharacterPlan, parent=None, selectable: bool = False):
        super(CharacterPlanBarWidget, self).__init__(parent)
        self._novel = novel
        self._character = character
        self._plan = plan
        self._selectable = selectable
        vbox(self)
        margins(self, left=5, right=5)
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
        sp(self._textSummary).h_exp()
        transparent(self._textSummary)
        self._textSummary.setPlaceholderText('Summarize this goal')
        self._textSummary.setAcceptRichText(False)
        self._textSummary.setText(self._plan.summary)
        self._textSummary.setReadOnly(self._selectable)
        self._textSummary.textChanged.connect(self._summaryChanged)

        self._btnContext = DotsMenuButton()
        menu = MenuWidget(self._btnContext)
        menu.addAction(action('Delete', IconRegistry.trash_can_icon(), self.removed.emit))

        self._wdgHeader.layout().addWidget(self._lblEmoji, alignment=Qt.AlignmentFlag.AlignTop)
        self._wdgHeader.layout().addWidget(self._textSummary, alignment=Qt.AlignmentFlag.AlignTop)
        self._wdgHeader.layout().addWidget(spacer())
        self._wdgHeader.layout().addWidget(self._btnContext, alignment=Qt.AlignmentFlag.AlignTop)

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
        self.layout().addWidget(line())
        self.layout().addWidget(self._wdgBar)

        if self._selectable:
            self._btnContext.setHidden(True)
        else:
            self._wdgHeader.installEventFilter(VisibilityToggleEventFilter(self._btnContext, self._wdgHeader))

        self.repo = RepositoryPersistenceManager.instance()

    def plan(self) -> CharacterPlan:
        return self._plan

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
                wdg.setForward(True)
            else:
                wdg.setForward(False)
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
        goalWdg = CharacterGoalWidget(self._novel, goal, selectable=self._selectable)
        goalWdg.addAfter.connect(partial(self._addNewGoal, goalWdg))
        goalWdg.addBefore.connect(partial(self._addNewGoalBefore, goalWdg))
        goalWdg.subtasksChanged.connect(self.update)
        goalWdg.delete.connect(partial(self._deleteGoal, goalWdg))
        goalWdg.selected.connect(partial(self.goalSelected.emit, goalWdg))
        goalWdg.subtaskSelected.connect(self.subtaskSelected.emit)
        self._goalWidgets[goal] = goalWdg
        return goalWdg

    def _addNewGoal(self, ref: CharacterGoalWidget):
        i = self._plan.goals.index(ref.goal())
        self._addNewGoalAt(i + 1)

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
        goalWidget.lineText.setFocus()

        self.repo.update_novel(self._novel)

    def _deleteGoal(self, wdg: CharacterGoalWidget):
        goal = wdg.goal()
        self._plan.goals.remove(goal)
        self._goalWidgets.pop(goal)
        self._wdgBar.layout().removeWidget(wdg)
        gc(wdg)

        if not self._plan.goals:
            self._btnAdd.setVisible(True)

    def _summaryChanged(self):
        self._plan.summary = self._textSummary.toPlainText()


class CharacterPlansWidget(QWidget):
    def __init__(self, novel: Novel, character: Character, parent=None):
        super(CharacterPlansWidget, self).__init__(parent)
        self._novel = novel
        self._character = character
        vbox(self)

        self._btnAdd = QPushButton()
        self._btnAdd.setProperty('base', True)
        self._btnAdd.setProperty('positive', True)
        self._btnAdd.setIcon(IconRegistry.plus_icon('white'))
        pointy(self._btnAdd)
        self._btnAdd.setText('Add new goal')
        menu = QMenu()
        menu.addAction('External goal', self._addNewPlan)
        menu.addAction('Internal goal', lambda: self._addNewPlan(external=False))
        self._btnAdd.setMenu(menu)
        self._btnAdd.installEventFilter(ButtonPressResizeEventFilter(self._btnAdd))
        self.layout().addWidget(group(self._btnAdd, spacer()))

        for plan in self._character.plans:
            bar = self.__initPlanWidget(plan)
            self.layout().addWidget(bar)
        self.layout().addWidget(vspacer())

    def _addNewPlan(self, external: bool = True):
        plan = CharacterPlan(external=external)
        self._character.plans.append(plan)

        bar = self.__initPlanWidget(plan)
        self.layout().insertWidget(self.layout().count() - 1, bar)

    def _removePlan(self, wdg: CharacterPlanBarWidget):
        self._character.plans.remove(wdg.plan())
        fade_out_and_gc(self, wdg)

    def __initPlanWidget(self, plan: CharacterPlan) -> CharacterPlanBarWidget:
        bar = CharacterPlanBarWidget(self._novel, self._character, plan)
        bar.removed.connect(partial(self._removePlan, bar))
        return bar


class CharacterPlansSelectorWidget(QWidget):
    goalSelected = pyqtSignal(CharacterGoal)

    def __init__(self, novel: Novel, character: Character, parent=None):
        super(CharacterPlansSelectorWidget, self).__init__(parent)
        self._novel = novel
        self._character = character
        vbox(self)

        for plan in self._character.plans:
            bar = CharacterPlanBarWidget(self._novel, self._character, plan, selectable=True)
            bar.goalSelected.connect(self._goalSelected)
            bar.subtaskSelected.connect(self._subtaskSelected)
            self.layout().addWidget(bar)
        self.layout().addWidget(vspacer())

    def _goalSelected(self, wdg: CharacterGoalWidget, selected: bool):
        if selected:
            self.goalSelected.emit(wdg.goal())

    def _subtaskSelected(self, wdg: CharacterSubtaskWidget, selected: bool):
        if selected:
            self.goalSelected.emit(wdg.subtask())


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
            self.widget = CharacterPlansSelectorWidget(novel, character)
            self.setCentralWidget(self.widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
