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

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QMainWindow, QApplication, QLabel
from qthandy import vbox, vspacer, hbox, spacer, flow, transparent, margins

from src.main.python.plotlyst.core.domain import Character, CharacterGoal, Novel, CharacterPlan, Goal
from src.main.python.plotlyst.view.widget.input import AutoAdjustableTextEdit
from src.main.python.plotlyst.view.widget.utility import IconSelectorButton


class CharacterGoalWidget(QWidget):
    def __init__(self, novel: Novel, goal: CharacterGoal, parent=None):
        super(CharacterGoalWidget, self).__init__(parent)
        self._novel = novel
        self._goal = goal

        vbox(self)
        self._wdgCenter = QWidget()
        hbox(self._wdgCenter)
        self._iconSelector = IconSelectorButton()
        self._iconSelector.selectIcon('mdi.target', 'darkBlue')
        self._wdgCenter.layout().addWidget(self._iconSelector)

        self.layout().addWidget(self._wdgCenter)


class CharacterPlanBarWidget(QWidget):
    def __init__(self, novel: Novel, character: Character, plan: CharacterPlan, parent=None):
        super(CharacterPlanBarWidget, self).__init__(parent)
        self._novel = novel
        self._character = character
        self._plan = plan
        vbox(self)

        self._wdgHeader = QWidget()
        hbox(self._wdgHeader)
        self._lblEmoji = QLabel('emoji')
        self._textSummary = AutoAdjustableTextEdit()
        transparent(self._textSummary)
        self._textSummary.setPlaceholderText('Summarize this goal')
        self._wdgHeader.layout().addWidget(self._lblEmoji, alignment=Qt.AlignmentFlag.AlignTop)
        self._wdgHeader.layout().addWidget(self._textSummary, alignment=Qt.AlignmentFlag.AlignTop)
        self._wdgHeader.layout().addWidget(spacer())

        self._wdgBar = QWidget()
        flow(self._wdgBar)
        margins(self._wdgBar, left=20, top=10, bottom=10)
        for goal in self._plan.goals:
            goalWdg = CharacterGoalWidget(self._novel, goal)
            self._wdgBar.layout().addWidget(goalWdg)

        self.layout().addWidget(self._wdgHeader)
        self.layout().addWidget(self._wdgBar)


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
            character.plans.append(plan)
            self.widget = CharacterPlansWidget(novel, character)
            self.setCentralWidget(self.widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
