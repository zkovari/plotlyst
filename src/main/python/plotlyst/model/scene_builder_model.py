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
from PyQt5.QtCore import QModelIndex, Qt, QMimeData, QByteArray, QSize
from PyQt5.QtGui import QIcon
from anytree import Node
from overrides import overrides

from src.main.python.plotlyst.core.domain import Character, Scene, NpcCharacter, SceneBuilderElement
from src.main.python.plotlyst.model.tree_model import TreeItemModel
from src.main.python.plotlyst.view.common import emoji_font
from src.main.python.plotlyst.view.dialog.scene_builder_edition import SceneElementEditionDialog, DialogEditionDialog, \
    CharacterBasedEditionDialog, SceneElementEditionResult
from src.main.python.plotlyst.view.icons import avatars, IconRegistry


class SceneInventoryNode(Node):
    def __init__(self, name: str, emoji_name: str, parent):
        super().__init__(name, parent)
        self.emoji = emoji.emojize(emoji_name)
        self.character: Optional[Character] = None
        self.tension: bool = False
        self.suspense: bool = False
        self.stakes: bool = False


class CharacterEntryNode(SceneInventoryNode):
    def __init__(self, parent: Node):
        super().__init__('Character entry', ':door:', parent)


class DialogSpeechNode(SceneInventoryNode):
    def __init__(self, parent: Node):
        super().__init__('Speech', ':speaking_head:', parent)


class DialogActionBeatNode(SceneInventoryNode):
    def __init__(self, parent: Node):
        super().__init__('Action beat', ':clapping_hands:', parent)


class ReactionNode(SceneInventoryNode):
    def __init__(self, parent: Node):
        super().__init__('Reaction', ':blue_circle:', parent)
        SceneInventoryNode('Feeling', ':broken_heart:', self)
        SceneInventoryNode('Reflex', ':hand_with_fingers_splayed:', self)
        SceneInventoryNode('Rational action', ':play_button:', self)
        SceneInventoryNode('Monolog', ':thinking_face:', self)
        DialogSpeechNode(self)


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
            if role == Qt.SizeHintRole:
                rows = int(len(node.name) / 35)
                height = 20 + 20 * rows
                return QSize(150, height)
            if role == Qt.DecorationRole:
                if node.character:
                    if isinstance(node.character, NpcCharacter):
                        return IconRegistry.portrait_icon()
                    return QIcon(avatars.pixmap(node.character))

    @overrides
    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        node = indexes[0].internalPointer()
        mime_data = QMimeData()
        mime_data.setData(self.MimeType, QByteArray(pickle.dumps(node)))
        return mime_data

    @overrides
    def mimeTypes(self) -> List[str]:
        return [self.MimeType]

    def deleteItem(self, index: QModelIndex):
        node = index.internalPointer()
        node.parent = None

        self.modelReset.emit()


class SceneBuilderInventoryTreeModel(_SceneBuilderTreeModel):

    def __init__(self):
        super(SceneBuilderInventoryTreeModel, self).__init__()

        CharacterEntryNode(self.root)
        dialog = Node('Dialog', self.root)
        DialogSpeechNode(dialog)
        DialogActionBeatNode(dialog)
        sensor = Node('Sensors', self.root)
        SceneInventoryNode('Sight', ':eyes:', sensor)
        SceneInventoryNode('Sound', ':speaker_high_volume:', sensor)
        SceneInventoryNode('Smell', ':nose:', sensor)
        SceneInventoryNode('Taste', ':tongue:', sensor)
        SceneInventoryNode('Touch', ':handshake:', sensor)
        ReactionNode(self.root)
        # SceneInventoryNode('Feeling', ':broken_heart:', reaction)
        # SceneInventoryNode('Reflex', ':hand_with_fingers_splayed:', reaction)
        # SceneInventoryNode('Rational action', ':play_button:', reaction)
        # SceneInventoryNode('Monolog', ':thinking_face:', reaction)

        SceneInventoryNode('Action', ':play_button:', self.root)
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

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        node = index.internalPointer()
        if isinstance(node, SceneInventoryNode):
            return flags | Qt.ItemIsDragEnabled
        return flags


class SceneBuilderPaletteTreeModel(_SceneBuilderTreeModel):

    def __init__(self, scene: Scene):
        super(SceneBuilderPaletteTreeModel, self).__init__(None)
        self.scene = scene

    def setElements(self, elements: List[SceneBuilderElement]):
        for el in elements:
            self._createNode(el, self.root)

        self.modelReset.emit()

    def _createNode(self, element: SceneBuilderElement, parent: Node):
        node = DialogSpeechNode(parent)
        node.name = element.text
        node.stakes = element.has_stakes
        node.tension = element.has_tension
        node.suspense = element.has_suspense

        for child in element.children:
            self._createNode(child, node)

    @overrides
    def columnCount(self, parent: QModelIndex) -> int:
        return 3

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        node = index.internalPointer()
        if isinstance(node, SceneInventoryNode):
            return flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsEditable
        return flags | Qt.ItemIsDropEnabled

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        node = index.internalPointer()
        if isinstance(node, CharacterEntryNode):
            node.name = value.name
            node.character = value
        else:
            node.name = value

        self.modelReset.emit()
        return True

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
        node: Optional[SceneInventoryNode] = pickle.loads(data.data(self.MimeType))
        parent_node = self.root
        if isinstance(data, InternalSceneElementMimeData):
            node = data.node
            node.parent = None
            if parent.isValid():
                parent_node = parent.internalPointer()
            node.parent = parent_node
        else:  # to the end
            if parent.isValid():
                parent_node = parent.internalPointer()

            if isinstance(node, (DialogSpeechNode, DialogActionBeatNode)):
                result = DialogEditionDialog().display(self.scene)
            elif isinstance(node, CharacterEntryNode):
                result = CharacterBasedEditionDialog().display(self.scene)
            elif isinstance(node, ReactionNode):
                result = SceneElementEditionResult('Reaction')
            else:
                result = SceneElementEditionDialog().display(self.scene)
            if result is None:
                return False

            node.parent = None
            node.parent = parent_node
            node.character = result.character
            node.name = result.text

        if node and row >= 0:
            self._repositionNodeUnder(node, parent_node, row)

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
