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
import pickle
from typing import Any, List

import emoji
from PyQt5.QtCore import QModelIndex, Qt, QMimeData, QByteArray, QPersistentModelIndex
from anytree import Node
from overrides import overrides

from src.main.python.plotlyst.model.tree_model import TreeItemModel
from src.main.python.plotlyst.view.common import emoji_font


class SceneInventoryNode(Node):
    def __init__(self, name: str, emoji_name: str, parent):
        super().__init__(name, parent)
        self.emoji = emoji.emojize(emoji_name)


class InternalSceneElementMimeData(QMimeData):
    def __init__(self, node: SceneInventoryNode):
        self.node = node
        super().__init__()


class _SceneBuilderTreeModel(TreeItemModel):
    MimeType: str = 'application/scene_element'

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.FontRole:
            return emoji_font(12)
        node = index.internalPointer()
        if isinstance(node, SceneInventoryNode):
            return self._dataForInventoryNode(node, index.column(), role)
        elif index.column() == 0:
            return super(_SceneBuilderTreeModel, self).data(index, role)

    def _dataForInventoryNode(self, node: SceneInventoryNode, column: int, role: int):
        if column == 0:
            if role == Qt.DisplayRole:
                return f'{node.emoji}{node.name}'

    @overrides
    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        node = indexes[0].internalPointer()
        mime_data = QMimeData()
        mime_data.setData(self.MimeType, QByteArray(pickle.dumps(node)))
        return mime_data

    @overrides
    def mimeTypes(self) -> List[str]:
        return [self.MimeType]


class SceneBuilderInventoryTreeModel(_SceneBuilderTreeModel):

    def __init__(self):
        super(SceneBuilderInventoryTreeModel, self).__init__()

        SceneInventoryNode('Character entry', ':door:', self.root)
        SceneInventoryNode('Dialog', ':speaking_head:', self.root)
        sensor = Node('Sensor', self.root)
        SceneInventoryNode('Sight', ':eyes:', sensor)
        # SceneInventoryNode('External conflict', ':crossed_swords:', self.root)
        # SceneInventoryNode('Internal conflict', ':angry_face_with_horns:', self.root)
        SceneInventoryNode('Emotional change', ':chart_increasing:', self.root)
        # SceneInventoryNode('Tension', ':confounded_face:', self.root)
        # SceneInventoryNode('Suspense', ':flushed_face:', self.root)
        # SceneInventoryNode('Stakes', ':face_screaming_in_fear:', self.root)
        SceneInventoryNode('Goal', ':bullseye:', self.root)
        SceneInventoryNode('Disaster', ':bomb:', self.root)
        SceneInventoryNode('Resolution', ':trophy:', self.root)
        # SceneInventoryNode('Monolog', ':thinking_face:', self.root)
        SceneInventoryNode('Decision', ':brain:', self.root)
        SceneInventoryNode('Ending', ':chequered_flag:', self.root)
        # SceneInventoryNode('Dialog', ':speech_balloon:', self.root)
        # SceneInventoryNode('Dialog', ':speech_balloon:', self.root)
        # SceneInventoryNode('Dialog', ':speech_balloon:', self.root)
        # SceneInventoryNode('Dialog', ':speech_balloon:', self.root)

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        node = index.internalPointer()
        if isinstance(node, SceneInventoryNode):
            return flags | Qt.ItemIsDragEnabled
        return flags


class SceneBuilderPaletteTreeModel(_SceneBuilderTreeModel):
    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        node = index.internalPointer()
        if isinstance(node, SceneInventoryNode):
            return flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return flags | Qt.ItemIsDropEnabled

    @overrides
    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        node = indexes[0].internalPointer()
        mime_data = InternalSceneElementMimeData(node)
        mime_data.setData(self.MimeType, QByteArray(pickle.dumps(node)))
        return mime_data

    @overrides
    def canDropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int,
                        parent: QModelIndex) -> bool:
        return True
        # if row >= 0 and parent.internalPointer() == self.root:
        #     return False
        # if not data.hasFormat(self.MimeType):
        #     return False
        # if not isinstance(parent.internalPointer(), (ChapterNode, UncategorizedChapterNode)):
        #     return False

        # return True

    @overrides
    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int,
                     parent: QModelIndex) -> bool:
        dropped_node: SceneInventoryNode = pickle.loads(data.data(self.MimeType))
        if isinstance(data, InternalSceneElementMimeData):
            print('internal drop')
            return True
        if not parent.isValid() and row < 0:  # to the end
            print(f'not valid parent {row}')
            SceneInventoryNode(dropped_node.name, dropped_node.emoji, self.root)
        elif row >= 0:
            print('in between')
            # parent_node: Node = parent.internalPointer()
            new_node = SceneInventoryNode(dropped_node.name, dropped_node.emoji, self.root)
            children_list = list(self.root.children)
            old_index = children_list.index(new_node)
            new_index = row
            # if old_parent_node is parent_node and new_index > old_index:
            #     new_index -= 1
            children_list[old_index], children_list[new_index] = children_list[new_index], children_list[old_index]
            self.root.children = children_list
        else:
            print('on parent')
            return False
        self.layoutAboutToBeChanged.emit([QPersistentModelIndex(parent)])
        self.layoutChanged.emit([QPersistentModelIndex(parent)])
        return True
