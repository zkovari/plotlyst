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
from typing import Any

import qtawesome
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant
from overrides import overrides

from novel_outliner.core.domain import Novel


class StoryLinesScenesDistributionTableModel(QAbstractTableModel):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.story_lines)

    @overrides
    def columnCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.scenes) + 1

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return

        if index.column() == 0:
            if role == Qt.DisplayRole:
                return self.novel.story_lines[index.row()].text
        elif role == Qt.ToolTipRole:
            return f'{index.column()}. {self.novel.scenes[index.column() - 1].title}'
        elif role == Qt.DecorationRole:
            if self.novel.story_lines[index.row()] in self.novel.scenes[index.column() - 1].story_lines:
                if self.novel.scenes[index.column() - 1].wip:
                    color = '#f2f763'
                else:
                    color = 'black'
                if len(self.novel.scenes[index.column() - 1].story_lines) == 1:
                    return qtawesome.icon('mdi.circle-medium', color=color)
                else:
                    return qtawesome.icon('mdi.circle-outline', color=color)
        return QVariant()
