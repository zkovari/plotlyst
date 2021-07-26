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
from typing import Any, List, Optional

import emoji
from PyQt5.QtCore import QModelIndex, Qt, QMimeData, QByteArray
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
        SceneInventoryNode('Sound', ':speaker_high_volume:', sensor)
        SceneInventoryNode('Smell', ':nose:', sensor)
        SceneInventoryNode('Taste', ':tongue:', sensor)
        SceneInventoryNode('Touch', ':handshake:', sensor)
        reaction = SceneInventoryNode('Reaction', ':blue_circle:', self.root)
        SceneInventoryNode('Feeling', ':broken_heart:', reaction)
        SceneInventoryNode('Reflex', ':hand_with_fingers_splayed:', reaction)
        SceneInventoryNode('Rational action', ':left-facing_fist:', reaction)
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
    def columnCount(self, parent: QModelIndex) -> int:
        return 3

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
        dragged_node: SceneInventoryNode = pickle.loads(data.data(self.MimeType))
        node: Optional[SceneInventoryNode] = None
        if isinstance(data, InternalSceneElementMimeData):
            node = data.node
            node.parent = None
            if not parent.isValid():
                node.parent = self.root
            else:
                node.parent = parent.internalPointer()
        else:  # to the end
            if not parent.isValid():
                node = SceneInventoryNode(dragged_node.name, dragged_node.emoji, self.root)
            else:
                node = SceneInventoryNode(dragged_node.name, dragged_node.emoji, parent.internalPointer())
            for child in dragged_node.children:
                SceneInventoryNode(child.name, child.emoji, node)

        if node and row >= 0:
            self._repositionNodeUnder(node, self.root, row)

        self.modelReset.emit()
        return True

    def _repositionNodeUnder(self, node, parent, row: int):
        children_list = list(parent.children)
        old_index = children_list.index(node)
        new_index = row
        if old_index < new_index:
            new_index -= 1
        children_list[old_index], children_list[new_index] = children_list[new_index], children_list[old_index]
        parent.children = children_list
