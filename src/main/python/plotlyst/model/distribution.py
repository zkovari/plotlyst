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
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QIcon, QBrush, QColor
from overrides import overrides

from src.main.python.plotlyst.core.domain import Conflict, ConflictType, SceneGoal
from src.main.python.plotlyst.model.common import DistributionModel
from src.main.python.plotlyst.view.common import text_color_with_bg_color
from src.main.python.plotlyst.view.icons import avatars, IconRegistry


class CharactersScenesDistributionTableModel(DistributionModel):

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.characters)

    @overrides
    def _dataForTag(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if role == Qt.DecorationRole:
            return QIcon(avatars.pixmap(self.novel.characters[index.row()]))
        if role == Qt.ToolTipRole:
            return self.novel.characters[index.row()].name
        elif role == Qt.DisplayRole or role == self.SortRole:
            return super(CharactersScenesDistributionTableModel, self).data(index, role=self.SortRole)

    @overrides
    def _match_by_row_col(self, row: int, column: int):
        in_char = self.novel.characters[row] in self.novel.scenes[column - 2].characters
        pov = self.novel.characters[row] == self.novel.scenes[column - 2].pov
        return in_char or pov


class GoalScenesDistributionTableModel(DistributionModel):

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.scene_goals)

    @overrides
    def _dataForTag(self, index: QModelIndex, role: int = Qt.DisplayRole):
        goal: SceneGoal = self.novel.scene_goals[index.row()]

        if role == Qt.DecorationRole and goal.icon:
            return IconRegistry.from_name(goal.icon, goal.icon_color)
        if role == Qt.DisplayRole:
            return goal.text

    @overrides
    def _dataForMeta(self, index: QModelIndex, role: int = Qt.DisplayRole):
        goal: SceneGoal = self.novel.scene_goals[index.row()]
        if role == Qt.DecorationRole:
            if goal.icon:
                return IconRegistry.from_name(goal.icon, goal.icon_color)
            else:
                return IconRegistry.goal_icon()

    @overrides
    def _match_by_row_col(self, row: int, column: int):
        for agenda in self.novel.scenes[column - 2].agendas:
            for item in agenda.items:
                if self.novel.scene_goals[row] in item.goals:
                    return True
        return False


class ConflictScenesDistributionTableModel(DistributionModel):

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.conflicts)

    @overrides
    def _dataForTag(self, index: QModelIndex, role: int = Qt.DisplayRole):
        conflict: Conflict = self.novel.conflicts[index.row()]
        if role == Qt.DecorationRole:
            if conflict.type == ConflictType.CHARACTER:
                return QIcon(avatars.pixmap(conflict.conflicting_character(self.novel)))
            elif conflict.type == ConflictType.SELF:
                return IconRegistry.conflict_self_icon()
            elif conflict.type == ConflictType.NATURE:
                return IconRegistry.conflict_nature_icon()
            elif conflict.type == ConflictType.SOCIETY:
                return IconRegistry.conflict_society_icon()
            elif conflict.type == ConflictType.TECHNOLOGY:
                return IconRegistry.conflict_technology_icon()
            elif conflict.type == ConflictType.SUPERNATURAL:
                return IconRegistry.conflict_supernatural_icon()

        if role == Qt.ToolTipRole:
            return conflict.type
        elif role == Qt.DisplayRole:
            return conflict.text

    @overrides
    def _dataForMeta(self, index: QModelIndex, role: int = Qt.DisplayRole):
        conflict: Conflict = self.novel.conflicts[index.row()]
        if role == Qt.DecorationRole:
            return QIcon(avatars.pixmap(conflict.character(self.novel)))

    @overrides
    def _match_by_row_col(self, row: int, column: int):
        for agenda in self.novel.scenes[column - 2].agendas:
            for item in agenda.items:
                if self.novel.conflicts[row] in item.conflicts:
                    return True
        return False


class TagScenesDistributionTableModel(DistributionModel):

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.tags)

    @overrides
    def _dataForTag(self, index: QModelIndex, role: int = Qt.DisplayRole):
        tag = self.novel.tags[index.row()]
        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            return tag.text
        if role == Qt.DecorationRole:
            if tag.icon:
                return IconRegistry.from_name(tag.icon, color=tag.icon_color)
        if role == Qt.ForegroundRole:
            if tag.color_hexa:
                text_color = text_color_with_bg_color(tag.color_hexa)
                return QBrush(QColor(text_color))
        if role == Qt.BackgroundRole:
            if tag.color_hexa:
                return QBrush(QColor(tag.color_hexa))

    @overrides
    def _match_by_row_col(self, row: int, column: int):
        return self.novel.tags[row].text in self.novel.scenes[column - 2].tags
