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
from typing import Dict

import emoji
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPaintEvent, QPainter, QPen, QColor, QPainterPath, QResizeEvent, QShowEvent
from PyQt6.QtWidgets import QWidget, QMainWindow, QApplication, QLabel, QLineEdit, QSizePolicy
from overrides import overrides
from qthandy import vbox, vspacer, hbox, spacer, flow, transparent, margins, line, retain_when_hidden

from src.main.python.plotlyst.core.domain import Character, CharacterGoal, Novel, CharacterPlan, Goal
from src.main.python.plotlyst.view.common import emoji_font
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit
from src.main.python.plotlyst.view.widget.utility import IconSelectorButton


class CharacterGoalWidget(QWidget):
    def __init__(self, novel: Novel, goal: CharacterGoal, parent=None):
        super(CharacterGoalWidget, self).__init__(parent)
        self._novel = novel
        self._goal = goal

        vbox(self, 0)
        self._wdgCenter = QWidget()
        hbox(self._wdgCenter, 0, 0)
        self.iconSelector = IconSelectorButton()
        self.iconSelector.selectIcon('mdi.target', 'darkBlue')
        self.lineText = QLineEdit()
        self.lineText.setPlaceholderText('Objective')
        self.hLine = line()
        retain_when_hidden(self.hLine)
        self.hLine.setHidden(True)
        transparent(self.lineText)

        self._wdgCenter.layout().addWidget(self.iconSelector)
        self._wdgCenter.layout().addWidget(group(self.lineText, self.hLine, vertical=False))

        self.layout().addWidget(self._wdgCenter)

    def entryPoint(self) -> QPointF:
        return self.hLine.mapToGlobal(self.hLine.pos()).toPointF()


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
        flow(self._wdgBar, spacing=0)
        margins(self._wdgBar, left=20, top=10, bottom=10)
        self._goalWidgets: Dict[CharacterGoal, CharacterGoalWidget] = {}
        for goal in self._plan.goals:
            goalWdg = CharacterGoalWidget(self._novel, goal)
            self._goalWidgets[goal] = goalWdg
            self._wdgBar.layout().addWidget(goalWdg)

        self.layout().addWidget(self._wdgHeader)
        self.layout().addWidget(self._wdgBar)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen()
        pen.setColor(QColor('darkBlue'))
        pen.setWidth(3)
        painter.setPen(pen)

        path = QPainterPath()

        for i, goal in enumerate(self._plan.goals):
            wdg = self._goalWidgets[goal]
            pos: QPointF = wdg.mapTo(self, wdg.hLine.pos()).toPointF()
            pos.setY(pos.y() + wdg.layout().contentsMargins().top())
            pos.setX(pos.x() + wdg.layout().contentsMargins().left())
            if i == 0:
                path.moveTo(pos)
            else:
                path.lineTo(pos)
            pos.setX(pos.x() + wdg.hLine.width() + wdg.iconSelector.width())
            path.lineTo(pos)

        painter.drawPath(path)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if self._firstShow:
            self._rearrange()
            self._firstShow = False

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        self._rearrange()

    def _rearrange(self):
        first_y = 0
        last_y = 0
        for i, goal in enumerate(self._plan.goals):
            wdg = self._goalWidgets[goal]
            if i == 0:
                first_y = wdg.pos().y()
                last_y = first_y
                continue

            margins(wdg, top=40 if wdg.pos().y() > first_y else 0)

            if wdg.pos().y() > last_y:
                last_y = wdg.pos().y()
                margins(wdg, left=40, top=40)
            else:
                margins(wdg, left=0)


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
            plan.goals.append(CharacterGoal(goal_id=goal.id))
            plan.goals.append(CharacterGoal(goal_id=goal.id))
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
