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

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QVariant, Qt
from anytree import Node
from overrides import overrides


class TreeItemModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root = Node('root')

    def rootNode(self) -> Node:
        return self.root

    def setRootNode(self, node: Node):
        self.root = node

    @overrides
    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_node: Node
        if not parent.isValid():
            parent_node = self.root
        else:
            parent_node = parent.internalPointer()

        if row >= len(parent_node.children):
            return QModelIndex()

        child_node = parent_node.children[row]
        return self.createIndex(row, column, child_node)

    @overrides
    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_node: Node = index.internalPointer()
        parent_node: Node = child_node.parent

        if parent_node == self.root:
            return QModelIndex()

        if not parent_node or parent_node.parent == self.root or not parent_node.parent:
            parent_node_index = 0
        else:
            parent_node_index = parent_node.parent.children.index(parent_node)

        return self.createIndex(parent_node_index, 0, parent_node)

    @overrides
    def rowCount(self, parent: QModelIndex) -> int:
        if parent.column() > 0:
            return 0

        parent_node: Node
        if not parent.isValid():
            parent_node = self.root
        else:
            parent_node = parent.internalPointer()
            
        return len(parent_node.children) if parent_node else 0

    @overrides
    def columnCount(self, parent: QModelIndex) -> int:
        if parent.isValid():
            node: Node = parent.internalPointer()
            return node.depth
        return 1

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            node: Node = index.internalPointer()
            return node.name

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return super().flags(index)
