from typing import Any, Set

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant
from overrides import overrides

from novel_outliner.core.domain import Novel, StoryLine


class NovelStoryLinesListModel(QAbstractListModel):
    StoryLineRole = Qt.UserRole + 1

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
