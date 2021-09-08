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
from typing import Any, Optional

from PyQt5.QtCore import QModelIndex, Qt
from anytree import Node
from overrides import overrides

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Document
from src.main.python.plotlyst.model.common import emit_column_changed_in_tree
from src.main.python.plotlyst.model.tree_model import TreeItemModel
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.worker.persistence import RepositoryPersistenceManager


class DocumentNode(Node):
    def __init__(self, doc: Document, parent: Node):
        super().__init__(doc.title, parent)
        self.document = doc


class DocumentsTreeModel(TreeItemModel):

    def __init__(self, novel: Novel):
        super(DocumentsTreeModel, self).__init__()
        self.novel = novel
        self._action_index: Optional[QModelIndex] = None
        self.repo = RepositoryPersistenceManager.instance()
        for doc in self.novel.documents:
            self._initNodes(doc, self.root)

    def _initNodes(self, doc: Document, parent_node: DocumentNode):
        new_node = DocumentNode(doc, parent_node)
        for child in doc.children:
            self._initNodes(child, new_node)

    @overrides
    def columnCount(self, parent: QModelIndex) -> int:
        return 2

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if index.column() == 0:
            if role == Qt.DisplayRole:
                return index.internalPointer().document.title
            return super(DocumentsTreeModel, self).data(index, role)
        if index.column() == 1 and self._action_index and index.row() == self._action_index.row() \
                and self._action_index.parent() == index.parent():
            if role == Qt.DecorationRole:
                return IconRegistry.plus_circle_icon('lightGrey')

    def displayAction(self, index: QModelIndex):
        if index.row() >= 0:
            if self._action_index and self._action_index.row() == index.row() \
                    and self._action_index.parent() == index.parent():  # same index
                return
            self._action_index = index
        else:
            self._action_index = None
        emit_column_changed_in_tree(self, 1, index)

    def insertDoc(self) -> QModelIndex:
        doc = Document('New Document')
        DocumentNode(doc, self.root)
        self.novel.documents.append(doc)
        self.modelReset.emit()
        self.repo.update_novel(self.novel)

        return self.index(self.rowCount(QModelIndex()) - 1, 0, QModelIndex())

    def insertDocUnder(self, index: QModelIndex) -> QModelIndex:
        node: DocumentNode = index.internalPointer()
        doc = Document('New Document')
        node.document.children.append(doc)
        DocumentNode(doc, node)
        self.modelReset.emit()
        self.repo.update_novel(self.novel)

        parent_index = self.index(index.row(), 0, index.parent())
        return self.index(len(node.document.children) - 1, 0, parent_index)

    def removeDoc(self, index: QModelIndex):
        node: DocumentNode = index.internalPointer()
        doc: Document = node.document

        parent_node = index.parent().internalPointer()
        if parent_node:
            parent_node.document.children.remove(doc)
        else:
            self.novel.documents.remove(doc)

        node.parent = None
        self._removeDoc(doc)

        self.modelReset.emit()

    def _removeDoc(self, doc: Document):
        for child in doc.children:
            self._removeDoc(child)
        json_client.delete_document(self.novel, doc)
