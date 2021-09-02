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
from abc import abstractmethod
from typing import Any, Set

from PyQt5.QtCore import QModelIndex, Qt, pyqtSignal, QAbstractTableModel
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, DramaticQuestion, SelectionItem
from src.main.python.plotlyst.event.core import emit_event
from src.main.python.plotlyst.events import StorylineCreatedEvent, NovelReloadRequestedEvent
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES
from src.main.python.plotlyst.worker.persistence import RepositoryPersistenceManager


class _NovelSelectionItemsModel(SelectionItemsModel):

    def __init__(self, novel: Novel):
        self.novel = novel
        self.repo = RepositoryPersistenceManager.instance()
        super().__init__()

    @abstractmethod
    @overrides
    def _newItem(self) -> QModelIndex:
        pass

    @abstractmethod
    @overrides
    def item(self, index: QModelIndex) -> SelectionItem:
        pass

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.DisplayRole) -> bool:
        updated = super().setData(index, value, role)
        if updated and role != Qt.CheckStateRole:
            self.repo.update_novel(self.novel)
        return updated


class NovelDramaticQuestionsModel(_NovelSelectionItemsModel):

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.dramatic_questions)

    @overrides
    def item(self, index: QModelIndex) -> SelectionItem:
        return self.novel.dramatic_questions[index.row()]

    @overrides
    def _newItem(self) -> QModelIndex:
        question = DramaticQuestion(text='')
        self.novel.dramatic_questions.append(question)
        question.color_hexa = STORY_LINE_COLOR_CODES[
            (len(self.novel.dramatic_questions) - 1) % len(STORY_LINE_COLOR_CODES)]
        self.repo.update_novel(self.novel)

        emit_event(StorylineCreatedEvent(self))

        return self.index(self.rowCount() - 1, 0)

    @overrides
    def remove(self, index: QModelIndex):
        super().remove(index)
        self.novel.dramatic_questions.pop(index.row())

        self.repo.update_novel(self.novel)
        emit_event(NovelReloadRequestedEvent(self))


class NovelTagsModel(_NovelSelectionItemsModel):

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.tags)

    @overrides
    def item(self, index: QModelIndex) -> SelectionItem:
        return self.novel.tags[index.row()]

    @overrides
    def _newItem(self) -> QModelIndex:
        tag = SelectionItem(text='')
        self.novel.tags.append(tag)
        self.repo.update_novel(self.novel)

        return self.index(self.rowCount() - 1, 0)

    @overrides
    def remove(self, index: QModelIndex):
        super().remove(index)
        self.novel.tags.pop(index.row())

        self.repo.update_novel(self.novel)
        emit_event(NovelReloadRequestedEvent(self))


class NovelDramaticQuestionsListModel(QAbstractTableModel):
    StoryLineRole = Qt.UserRole + 1
    selection_changed = pyqtSignal()
    ColText: int = 0

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.selected: Set[DramaticQuestion] = set()

    @overrides
    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.novel.dramatic_questions)

    @overrides
    def columnCount(self, parent: QModelIndex = ...) -> int:
        return 1

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return

        if role == self.StoryLineRole:
            return self.novel.dramatic_questions[index.row()]
        if index.column() == self.ColText:
            if role == Qt.DisplayRole:
                return self.novel.dramatic_questions[index.row()].text
            if role == Qt.CheckStateRole:
                if self.novel.dramatic_questions[index.row()] in self.selected:
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
                self.selected.add(self.novel.dramatic_questions[index.row()])
            elif value == Qt.Unchecked:
                self.selected.remove(self.novel.dramatic_questions[index.row()])
            self.selection_changed.emit()
            return True
        return False
