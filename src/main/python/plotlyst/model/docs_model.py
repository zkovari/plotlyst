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

from src.main.python.plotlyst.core.domain import Novel, Document
from src.main.python.plotlyst.model.tree_model import TreeItemModel
from src.main.python.plotlyst.view.icons import IconRegistry


class DocumentNode(Node):
    def __init__(self, doc: Document, parent: Node):
        super().__init__(doc.title, parent)
        self.document = doc


class DocumentsTreeModel(TreeItemModel):

    def __init__(self, novel: Novel):
        super(DocumentsTreeModel, self).__init__()
        self.novel = novel
        self._action_index: Optional[QModelIndex] = None
        for doc in self.novel.documents:
            DocumentNode(doc, self.root)

    @overrides
    def columnCount(self, parent: QModelIndex) -> int:
        return 2

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if index.column() == 0:
            return super(DocumentsTreeModel, self).data(index, role)
        if index.column() == 1 and self._action_index and index.row() == self._action_index.row():
            if role == Qt.DecorationRole:
                return IconRegistry.plus_circle_icon('lightGrey')

    def displayAction(self, index: QModelIndex):
        if index.row() >= 0:
            if self._action_index and self._action_index.row() == index.row():  # same index
                return
            self._action_index = index
        else:
            self._action_index = None
        self.modelReset.emit()
