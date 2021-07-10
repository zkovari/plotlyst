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
from typing import Any, Set

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant, pyqtSignal
from overrides import overrides

from novel_outliner.core.domain import Novel, StoryLine


class NovelStoryLinesListModel(QAbstractListModel):
    StoryLineRole = Qt.UserRole + 1
    selection_changed = pyqtSignal()

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.selected: Set[StoryLine] = set()

    @overrides
    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.novel.story_lines)

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return

        if role == self.StoryLineRole:
            return self.novel.story_lines[index.row()]
        if role == Qt.DisplayRole:
            return self.novel.story_lines[index.row()].text
        if role == Qt.CheckStateRole:
            if self.novel.story_lines[index.row()] in self.selected:
                return Qt.Checked
            return Qt.Unchecked

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        return flags | Qt.ItemIsUserCheckable

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.DisplayRole) -> bool:
        if role == Qt.CheckStateRole:
            if value == Qt.Checked:
                self.selected.add(self.novel.story_lines[index.row()])
            elif value == Qt.Unchecked:
                self.selected.remove(self.novel.story_lines[index.row()])
            self.selection_changed.emit()
            return True
        return False


class EditableNovelStoryLinesListModel(NovelStoryLinesListModel):

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        return flags | Qt.ItemIsEditable

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return

        if role == Qt.CheckStateRole:
            return QVariant()

        return super(EditableNovelStoryLinesListModel, self).data(index, role)

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.DisplayRole) -> bool:
        if role == Qt.EditRole:
            self.novel.story_lines[index.row()].text = value
            return True
        return False
