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

from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QKeyEvent
from overrides import overrides

from src.main.python.plotlyst.core.domain import Node, CharacterNode
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view.widget.graphics import NetworkScene
from src.main.python.plotlyst.view.widget.story_map.items import ItemType, MindMapNode, EventItem, StickerItem, \
    CharacterItem, SocketItem


class EventsMindMapScene(NetworkScene):
    editEvent = pyqtSignal(EventItem)
    editSticker = pyqtSignal(StickerItem)
    closeSticker = pyqtSignal()
    showItemEditor = pyqtSignal(MindMapNode)
    hideItemEditor = pyqtSignal()

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        if novel.characters:
            characterItem = CharacterItem(CharacterNode(50, 50), novel.characters[0])

            self.addItem(characterItem)
        eventItem = EventItem(Node(400, 100), ItemType.EVENT)
        self.addItem(eventItem)

        sticker = StickerItem(Node(200, 0), ItemType.COMMENT)
        self.addItem(sticker)

    @overrides
    def startLink(self, source: SocketItem):
        super().startLink(source)
        self.hideEditor()

    def editEventText(self, item: EventItem):
        self.editEvent.emit(item)

    def showEditor(self, item: MindMapNode):
        if not self._selectionMode:
            self.showItemEditor.emit(item)

    def hideEditor(self):
        if len(self.selectedItems()) == 1:
            self.hideItemEditor.emit()

    @overrides
    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        if not event.modifiers() and len(self.selectedItems()) == 1:
            item = self.selectedItems()[0]
            if isinstance(item, EventItem):
                self.editEvent.emit(item)

    def displayStickerMessage(self, sticker: StickerItem):
        self.editSticker.emit(sticker)

    def hideStickerMessage(self):
        self.closeSticker.emit()

    @overrides
    def _addNewItem(self, itemType: ItemType, scenePos: QPointF):
        if itemType == ItemType.CHARACTER:
            item = CharacterItem(self.toCharacterNode(scenePos), character=None)
        elif itemType in [ItemType.COMMENT, ItemType.TOOL, ItemType.COST]:
            item = StickerItem(Node(scenePos.x(), scenePos.y()), itemType)
        else:
            item = EventItem(self.toEventNode(scenePos), itemType)

        self.addItem(item)
        self.itemAdded.emit(itemType, item)
        self.endAdditionMode()

    @staticmethod
    def toEventNode(scenePos: QPointF) -> Node:
        node = Node(scenePos.x(), scenePos.y())
        node.x = node.x - EventItem.Margin - EventItem.Padding
        node.y = node.y - EventItem.Margin - EventItem.Padding
        return node

    @staticmethod
    def toCharacterNode(scenePos: QPointF) -> Node:
        node = Node(scenePos.x(), scenePos.y())
        node.x = node.x - CharacterItem.Margin
        node.y = node.y - CharacterItem.Margin
        return node
