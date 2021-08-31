"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from typing import List, Set

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy
from overrides import overrides

from src.main.python.plotlyst.core.domain import Scene, SelectionItem, Novel, SceneGoal
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.model.scenes_model import SceneGoalsModel
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.labels import LabelsEditorWidget, GoalLabel


class SceneGoalsWidget(LabelsEditorWidget):

    def __init__(self, novel: Novel, scene: Scene, parent=None):
        self.novel = novel
        self.scene = scene
        super(SceneGoalsWidget, self).__init__(Qt.Vertical, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setValue([x.text for x in self.scene.goals])
        self.btnEdit.setIcon(IconRegistry.goal_icon())
        self.btnEdit.setText('Add goal')
        self.setStyleSheet('SceneGoalsWidget {border: 0px;}')

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        return SceneGoalsModel(self.novel, self.scene)

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.novel.scene_goals

    @overrides
    def _addItems(self, items: Set[SceneGoal]):
        for item in items:
            self._wdgLabels.addLabel(GoalLabel(item))
        self.scene.goals.clear()
        self.scene.goals.extend(items)
