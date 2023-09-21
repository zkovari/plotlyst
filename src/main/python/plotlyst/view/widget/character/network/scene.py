"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

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

from PyQt6.QtCore import QPointF
from overrides import overrides

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Node, DiagramNodeType, PlaceholderCharacter
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.widget.graphics import NodeItem, NetworkScene, CharacterItem


class RelationsEditorScene(NetworkScene):
    # charactersChanged = pyqtSignal(RelationsNetwork)
    # charactersLinked = pyqtSignal(CharacterItem)

    def __init__(self, novel: Novel, parent=None):
        super(RelationsEditorScene, self).__init__(parent)
        self._novel = novel

        self.repo = RepositoryPersistenceManager.instance()

    @staticmethod
    def toCharacterNode(scenePos: QPointF) -> Node:
        node = Node(scenePos.x(), scenePos.y(), type=DiagramNodeType.CHARACTER)
        node.x = node.x - CharacterItem.Margin
        node.y = node.y - CharacterItem.Margin
        return node

    @overrides
    def _addNewItem(self, scenePos: QPointF, itemType: DiagramNodeType, subType: str = '') -> NodeItem:
        if itemType == DiagramNodeType.CHARACTER:
            item = CharacterItem(PlaceholderCharacter('Character'), self.toCharacterNode(scenePos))
            self.addItem(item)
            self.itemAdded.emit(itemType, item)
        self.endAdditionMode()

        return item

    @overrides
    def _addNode(self, node: Node):
        character = node.character(self._novel) if node.character_id else PlaceholderCharacter('Character')
        item = CharacterItem(character, node)
        self.addItem(item)

        return item

    @overrides
    def _load(self):
        json_client.load_diagram(self._novel, self._diagram)

    @overrides
    def _save(self):
        self.repo.update_diagram(self._novel, self._diagram)
