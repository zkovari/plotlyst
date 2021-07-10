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
        return len(parent_node.children)

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
