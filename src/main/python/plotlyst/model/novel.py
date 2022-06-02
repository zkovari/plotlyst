"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from typing import Any, List

from PyQt5.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt5.QtGui import QFont
from anytree import Node
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, SelectionItem, SceneStage, TagType, \
    Tag
from src.main.python.plotlyst.event.core import emit_event
from src.main.python.plotlyst.events import NovelReloadRequestedEvent
from src.main.python.plotlyst.model.common import SelectionItemsModel, DefaultSelectionItemsModel
from src.main.python.plotlyst.model.tree_model import TreeItemModel
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.icons import IconRegistry


class _NovelSelectionItemsModel(SelectionItemsModel):

    def __init__(self, novel: Novel):
        self.novel = novel
        self.repo = RepositoryPersistenceManager.instance()
        super().__init__()

    @abstractmethod
    @overrides
    def _newItem(self) -> QModelIndex:
        pass

    @overrides
    def _insertItem(self, row: int) -> QModelIndex:
        raise ValueError('Not supported operation')

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


class NovelTagsModel(_NovelSelectionItemsModel):

    def __init__(self, novel: Novel, tagType: TagType, tags: List[Tag]):
        super(NovelTagsModel, self).__init__(novel)
        self.tagType = tagType
        self.tags = tags

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.tags)

    @overrides
    def item(self, index: QModelIndex) -> SelectionItem:
        return self.tags[index.row()]

    @overrides
    def _newItem(self) -> QModelIndex:
        tag = Tag(text='', tag_type=self.tagType.text)
        self.novel.tags[self.tagType].append(tag)
        self.repo.update_novel(self.novel)

        return self.index(self.rowCount() - 1, 0)

    @overrides
    def remove(self, index: QModelIndex):
        super().remove(index)
        self.novel.tags[self.tagType].pop(index.row())

        self.repo.update_novel(self.novel)
        emit_event(NovelReloadRequestedEvent(self))


class TagTypeNode(Node):
    def __init__(self, tag_type: TagType, parent=None):
        super(TagTypeNode, self).__init__(tag_type.text, parent)
        self.tag_type = tag_type


class TagNode(Node):
    def __init__(self, tag: Tag, parent=None):
        super(TagNode, self).__init__(tag.text, parent)
        self.tag = tag


class NovelTagsTreeModel(TreeItemModel):
    selectionChanged = pyqtSignal()

    def __init__(self, novel: Novel, parent=None):
        super(NovelTagsTreeModel, self).__init__(parent)
        self.novel = novel
        for tag_type in novel.tags.keys():
            tag_type_node = TagTypeNode(tag_type, self.root)
            for tag in novel.tags[tag_type]:
                TagNode(tag, tag_type_node)

        self._checked = set()

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        node = index.internalPointer()
        if isinstance(node, TagTypeNode) and role == Qt.DecorationRole and node.tag_type.icon:
            return IconRegistry.from_name(node.tag_type.icon, node.tag_type.icon_color)
        elif isinstance(node, TagNode):
            if role == Qt.DecorationRole and node.tag.icon:
                if node.tag.color_hexa and node.tag.color_hexa.lower() != '#ffffff':
                    color = node.tag.color_hexa
                else:
                    color = node.tag.icon_color
                return IconRegistry.from_name(node.tag.icon, color)
            if role == Qt.CheckStateRole:
                return Qt.Checked if node.tag in self._checked else Qt.Unchecked
            if role == Qt.FontRole and node.tag in self._checked:
                font = QFont()
                font.setBold(True)
                return font

        return super(NovelTagsTreeModel, self).data(index, role)

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        node = index.internalPointer()
        if isinstance(node, TagNode):
            if role == Qt.CheckStateRole:
                if value == Qt.Checked:
                    self._checked.add(node.tag)
                elif value == Qt.Unchecked:
                    self._checked.remove(node.tag)
                self.selectionChanged.emit()
                return True

        return False

    def checkedTags(self) -> List[Tag]:
        return list(self._checked)

    def check(self, tag: Tag):
        self._checked.add(tag)
        self.selectionChanged.emit()
        self.modelReset.emit()

    def uncheck(self, tag: Tag):
        if tag in self._checked:
            self._checked.remove(tag)
            self.selectionChanged.emit()
            self.modelReset.emit()

    def toggle(self, tag: Tag):
        if tag in self._checked:
            self.uncheck(tag)
        else:
            self.check(tag)

    def clear(self):
        self._checked.clear()
        self.selectionChanged.emit()
        self.modelReset.emit()


class NovelStagesModel(DefaultSelectionItemsModel):
    @overrides
    def _newItem(self) -> QModelIndex:
        self._items.append(SceneStage(''))
        return self.index(self.rowCount() - 1, 0)
