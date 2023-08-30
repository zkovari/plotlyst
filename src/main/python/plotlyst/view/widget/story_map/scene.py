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
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QKeyEvent, QTransform
from overrides import overrides

from src.main.python.plotlyst.core.domain import Node, CharacterNode
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view.widget.graphics import ConnectorItem, NetworkScene
from src.main.python.plotlyst.view.widget.story_map.items import ItemType, MindMapNode, EventItem, StickerItem, \
    SelectorRectItem, PlaceholderItem, CharacterItem, SocketItem, ConnectableNode


class EventsMindMapScene(NetworkScene):
    editEvent = pyqtSignal(EventItem)
    editSticker = pyqtSignal(StickerItem)
    closeSticker = pyqtSignal()
    showItemEditor = pyqtSignal(MindMapNode)
    hideItemEditor = pyqtSignal()

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        self._selectionMode = False
        self._selectionRect = SelectorRectItem()
        self.addItem(self._selectionRect)
        self._selectionRect.setVisible(False)

        self._placeholder: Optional[PlaceholderItem] = None
        self._connectorPlaceholder: Optional[ConnectorItem] = None

        if novel.characters:
            characterItem = CharacterItem(CharacterNode(50, 50), novel.characters[0])

            self.addItem(characterItem)
        eventItem = EventItem(Node(400, 100), ItemType.EVENT)
        self.addItem(eventItem)

        sticker = StickerItem(Node(200, 0), ItemType.COMMENT)
        self.addItem(sticker)

    def linkSource(self) -> Optional[SocketItem]:
        if self._connectorPlaceholder is not None:
            return self._connectorPlaceholder.source()

    def startLink(self, source: SocketItem):
        self.hideEditor()
        self._linkMode = True
        self._placeholder = PlaceholderItem()
        self._placeholder.setVisible(False)
        self._placeholder.setEnabled(False)
        self.addItem(self._placeholder)
        self._connectorPlaceholder = ConnectorItem(source, self._placeholder)
        self.addItem(self._connectorPlaceholder)

        self._placeholder.setPos(source.scenePos())
        self._connectorPlaceholder.rearrange()

    def endLink(self):
        self._linkMode = False
        self.removeItem(self._connectorPlaceholder)
        self.removeItem(self._placeholder)
        self._connectorPlaceholder = None
        self._placeholder = None

    def link(self, target: SocketItem):
        connector = ConnectorItem(self._connectorPlaceholder.source(), target)
        self._connectorPlaceholder.source().addConnector(connector)
        target.addConnector(connector)
        self.addItem(connector)
        self.endLink()

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
        if event.key() == Qt.Key.Key_Escape:
            if self.linkMode():
                self.endLink()
            elif self.isAdditionMode():
                self.cancelItemAddition.emit()
            else:
                self.clearSelection()
        elif event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            for item in self.selectedItems():
                if isinstance(item, ConnectableNode):
                    item.removeConnectors()
                self.removeItem(item)
        elif not event.modifiers() and len(self.selectedItems()) == 1:
            item = self.selectedItems()[0]
            if isinstance(item, EventItem):
                self.editEvent.emit(item)

    @overrides
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if (not self.isAdditionMode() and not self.linkMode() and
                event.button() & Qt.MouseButton.LeftButton and not self.itemAt(event.scenePos(), QTransform())):
            self._selectionRect.start(event.scenePos())
            self._selectionMode = True
        elif event.button() & Qt.MouseButton.RightButton or event.button() & Qt.MouseButton.MiddleButton:
            # disallow view movement to clear item selection
            return
        super().mousePressEvent(event)

    @overrides
    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            self._placeholder.setPos(event.scenePos())
            self._connectorPlaceholder.rearrange()
        elif self._selectionMode:
            self._selectionRect.adjust(event.scenePos())
            self._selectionRect.setVisible(True)
            self._updateSelection()
        super().mouseMoveEvent(event)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            if event.button() & Qt.MouseButton.RightButton:
                self.endLink()
        elif self.isAdditionMode() and event.button() & Qt.MouseButton.RightButton:
            self.cancelItemAddition.emit()
        elif self._selectionMode and event.button() & Qt.MouseButton.LeftButton:
            self._selectionMode = False
            self._selectionRect.setVisible(False)
            self._updateSelection()
        elif self._additionMode is not None:
            self._addNewEvent(self._additionMode, event.scenePos())

        super().mouseReleaseEvent(event)

    def displayStickerMessage(self, sticker: StickerItem):
        self.editSticker.emit(sticker)

    def hideStickerMessage(self):
        self.closeSticker.emit()

    def _addNewEvent(self, itemType: ItemType, scenePos: QPointF):
        if itemType == ItemType.CHARACTER:
            item = CharacterItem(self.toCharacterNode(scenePos), character=None)
        elif itemType in [ItemType.COMMENT, ItemType.TOOL, ItemType.COST]:
            item = StickerItem(Node(scenePos.x(), scenePos.y()), itemType)
        else:
            item = EventItem(self.toEventNode(scenePos), itemType)

        self.addItem(item)
        self.itemAdded.emit(itemType, item)
        self.endAdditionMode()

    def _updateSelection(self):
        if not self._selectionRect.rect().isValid():
            return
        self.clearSelection()
        items_in_rect = self.items(self._selectionRect.rect(), Qt.ItemSelectionMode.IntersectsItemBoundingRect)
        for item in items_in_rect:
            item.setSelected(True)

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
