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
from typing import Optional

import qtanim
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QMouseEvent, QCursor
from PyQt6.QtWidgets import QWidget, QPushButton, QMenu, QWidgetAction
from overrides import overrides
from qthandy import hbox, pointy, gc, bold
from qthandy.filter import OpacityEventFilter
from qtmenu import ScrollableMenuWidget

from src.main.python.plotlyst.core.domain import Novel, Scene, GoalReference, Stake, CharacterGoal
from src.main.python.plotlyst.view.generated.scene_goal_stakes_ui import Ui_GoalReferenceStakesEditor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.character.plan import CharacterPlansSelectorWidget
from src.main.python.plotlyst.view.widget.labels import CharacterGoalLabel


class GoalStakesEditor(QWidget, Ui_GoalReferenceStakesEditor):
    def __init__(self, goalRef: GoalReference, parent=None):
        super(GoalStakesEditor, self).__init__(parent)
        self.setupUi(self)
        self.goalRef = goalRef
        self.refresh()
        bold(self.lblTitle)

        self.sliderPhysiological.valueChanged.connect(partial(self._stakeChanged, Stake.PHYSIOLOGICAL))
        self.sliderSecurity.valueChanged.connect(partial(self._stakeChanged, Stake.SAFETY))
        self.sliderBelonging.valueChanged.connect(partial(self._stakeChanged, Stake.BELONGING))
        self.sliderEsteem.valueChanged.connect(partial(self._stakeChanged, Stake.ESTEEM))
        self.sliderActualization.valueChanged.connect(partial(self._stakeChanged, Stake.SELF_ACTUALIZATION))
        self.sliderTranscendence.valueChanged.connect(partial(self._stakeChanged, Stake.SELF_TRANSCENDENCE))

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pass

    def refresh(self):
        for k, v in self.goalRef.stakes.items():
            if k == Stake.PHYSIOLOGICAL:
                self.sliderPhysiological.setValue(v)
            elif k == Stake.SAFETY:
                self.sliderSecurity.setValue(v)
            elif k == Stake.BELONGING:
                self.sliderBelonging.setValue(v)
            elif k == Stake.ESTEEM:
                self.sliderEsteem.setValue(v)
            elif k == Stake.SELF_ACTUALIZATION:
                self.sliderActualization.setValue(v)
            elif k == Stake.SELF_TRANSCENDENCE:
                self.sliderTranscendence.setValue(v)

    def _stakeChanged(self, stake: int, value: int):
        self.goalRef.stakes[stake] = value


class SceneGoalSelector(QWidget):
    goalSelected = pyqtSignal()

    def __init__(self, novel: Novel, scene: Scene, simplified: bool = False, parent=None):
        super(SceneGoalSelector, self).__init__(parent)
        self.novel = novel
        self.scene = scene
        self.characterGoal: Optional[CharacterGoal] = None
        self.goalRef: Optional[GoalReference] = None
        hbox(self)

        self.label: Optional[CharacterGoalLabel] = None

        self.btnLinkGoal = QPushButton(self)
        if not simplified:
            self.btnLinkGoal.setText('Track goal')
        self.layout().addWidget(self.btnLinkGoal)
        self.btnLinkGoal.setIcon(IconRegistry.goal_icon())
        pointy(self.btnLinkGoal)
        self.btnLinkGoal.setStyleSheet('''
                QPushButton {
                    border: 2px dotted grey;
                    border-radius: 6px;
                    font: italic;
                }
                QPushButton:hover {
                    border: 2px dotted darkBlue;
                    color: darkBlue;
                    font: normal;
                }
                QPushButton:pressed {
                    border: 2px solid white;
                }
            ''')

        self.btnLinkGoal.installEventFilter(OpacityEventFilter(parent=self.btnLinkGoal))
        # scrollArea = QScrollArea(self)
        # scrollArea.setWidgetResizable(True)
        # scrollArea.setMinimumSize(500, 300)
        menu = ScrollableMenuWidget(self.btnLinkGoal)
        self._goalSelector = CharacterPlansSelectorWidget(self.novel, self.scene.agendas[0].character(self.novel))
        menu.addWidget(self._goalSelector)
        # scrollArea.setBackgroundRole(QPalette.ColorRole.Light)
        # scrollArea.setWidget(self._goalSelector)
        # btn_popup(self.btnLinkGoal, scrollArea)

        self._goalSelector.goalSelected.connect(self._goalSelected)

    def setGoal(self, characterGoal: CharacterGoal, goalRef: GoalReference):
        self.characterGoal = characterGoal
        self.goalRef = goalRef
        self.label = CharacterGoalLabel(self.novel, self.characterGoal, self.goalRef, removalEnabled=True)
        pointy(self.label)
        self.label.clicked.connect(self._goalRefClicked)
        self.label.removalRequested.connect(self._remove)
        self.layout().addWidget(self.label)
        self.btnLinkGoal.setHidden(True)

    def _goalSelected(self, characterGoal: CharacterGoal):
        goal_ref = GoalReference(characterGoal.id)
        self.scene.agendas[0].goal_references.append(goal_ref)

        self.btnLinkGoal.menu().hide()
        self.setGoal(characterGoal, goal_ref)
        self.goalSelected.emit()

    def _goalRefClicked(self):
        menu = QMenu(self.label)
        action = QWidgetAction(menu)
        action.setDefaultWidget(GoalStakesEditor(self.goalRef))
        menu.addAction(action)
        menu.popup(QCursor.pos())

    def _remove(self):
        if self.parent():
            anim = qtanim.fade_out(self, duration=150)
            anim.finished.connect(self.__destroy)

    def __destroy(self):
        self.scene.agendas[0].remove_goal(self.characterGoal)
        self.parent().layout().removeWidget(self)
        gc(self)
