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
import math
from typing import Optional

from PyQt6.QtCore import QRectF, pyqtSignal, Qt, QPointF
from PyQt6.QtGui import QPainter, QPen, QKeyEvent, QColor, QBrush
from PyQt6.QtWidgets import QWidget, QStyleOptionGraphicsItem, QGraphicsSceneHoverEvent, \
    QGraphicsSceneMouseEvent
from overrides import overrides

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR, PLOTLYST_TERTIARY_COLOR, PLOTLYST_MAIN_COLOR
from src.main.python.plotlyst.core.domain import Character, Novel, RelationsNetwork, CharacterNode
from src.main.python.plotlyst.view.common import pointy
from src.main.python.plotlyst.view.icons import avatars
from src.main.python.plotlyst.view.widget.graphics import NodeItem, AbstractSocketItem, NetworkItemType, \
    NetworkScene


class CharacterNetworkItemType(NetworkItemType):
    CHARACTER = 1
    STICKER = 2


class PlaceholderCharacter(Character):
    pass


class SocketItem(AbstractSocketItem):
    Size: int = 20

    def __init__(self, parent=None):
        self._size = self.Size
        super().__init__(Qt.Edge.TopEdge, parent)
        pointy(self)
        self._hovered: bool = False

    @overrides
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = True
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = False
        self.update()

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        color = PLOTLYST_SECONDARY_COLOR if self._hovered else PLOTLYST_TERTIARY_COLOR
        painter.setPen(QPen(QColor(color), 1))
        painter.setBrush(QColor(color))

        radius = self.Size // 2
        painter.drawEllipse(QPointF(self.Size / 2, self.Size // 2), radius, radius)


class CharacterItem(NodeItem):
    Margin: int = 20
    PenWidth: int = 2

    def __init__(self, character: Character, node: CharacterNode, parent=None):
        super(CharacterItem, self).__init__(node, parent)
        self._character = character
        self._size: int = 68
        self._center = QPointF(self.Margin + self._size / 2, self.Margin + self._size / 2)
        self._outerRadius = self._size // 2 + self.Margin // 2

        self._animation = None
        self._linkMode: bool = False

        self._socket = SocketItem(self)
        self._socket.setVisible(False)

    def character(self) -> Character:
        return self._character

    def setCharacter(self, character: Character):
        self._character = character
        self.update()

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size + self.Margin * 2, self._size + self.Margin * 2)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self._linkMode:
            painter.setPen(QPen(QColor(PLOTLYST_TERTIARY_COLOR), self.PenWidth, Qt.PenStyle.DashLine))
            brush = QBrush(QColor(PLOTLYST_TERTIARY_COLOR), Qt.BrushStyle.Dense5Pattern)
            painter.setBrush(brush)
            painter.drawEllipse(self._center, self._outerRadius, self._outerRadius)
        elif self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.gray, self.PenWidth, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self.Margin, self.Margin, self._size, self._size, 2, 2)

        avatar = avatars.avatar(self._character)
        avatar.paint(painter, self.Margin, self.Margin, self._size, self._size)

    @overrides
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.relationsScene().linkMode():
            self.relationsScene().link(self)
        super(CharacterItem, self).mousePressEvent(event)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.relationsScene().linkMode() or event.modifiers() & Qt.KeyboardModifier.AltModifier:
            self._setConnectionEnabled(True)
            self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self._linkMode and not self.isSelected():
            self._setConnectionEnabled(False)
            self.update()

    @overrides
    def hoverMoveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self._linkMode:
            angle = math.degrees(math.atan2(
                event.pos().y() - self._center.y(), event.pos().x() - self._center.x()
            ))
            angle_radians = math.radians(angle)
            x = self._center.x() + self._outerRadius * math.cos(angle_radians) - SocketItem.Size // 2
            y = self._center.y() + self._outerRadius * math.sin(angle_radians) - SocketItem.Size // 2

            self.prepareGeometryChange()
            self._socket.setPos(x, y)
            self.update()

    def relationsScene(self) -> 'RelationsEditorScene':
        return self.scene()

    @overrides
    def _onSelection(self, selected: bool):
        super()._onSelection(selected)
        self._setConnectionEnabled(selected)

    def _setConnectionEnabled(self, enabled: bool):
        self._linkMode = enabled
        self._socket.setVisible(enabled)
        self.update()


class RelationsEditorScene(NetworkScene):
    charactersChanged = pyqtSignal(RelationsNetwork)
    charactersLinked = pyqtSignal(CharacterItem)

    def __init__(self, novel: Novel, parent=None):
        super(RelationsEditorScene, self).__init__(parent)
        self._novel = novel
        self._network: Optional[RelationsNetwork] = None

        node = CharacterNode(50, 50)
        if self._novel.characters:
            node.set_character(self._novel.characters[0])
            self.addItem(CharacterItem(self._novel.characters[0], node))

    def setNetwork(self, network: RelationsNetwork):
        self._network = network

    @overrides
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            for item in self.selectedItems():
                if isinstance(item, CharacterItem):
                    # self._network.nodes[:] = [node for node in self._network.nodes if
                    #                           node.character_id != item.character().id]
                    self.removeItem(item)
                    # self.charactersChanged.emit(self._network)

    def link(self, item: CharacterItem):
        self.charactersLinked.emit(item)

    @staticmethod
    def toCharacterNode(scenePos: QPointF) -> CharacterNode:
        node = CharacterNode(scenePos.x(), scenePos.y())
        node.x = node.x - CharacterItem.Margin
        node.y = node.y - CharacterItem.Margin
        return node

    @overrides
    def _addNewItem(self, itemType: CharacterNetworkItemType, scenePos: QPointF):
        if itemType == CharacterNetworkItemType.CHARACTER:
            item = CharacterItem(PlaceholderCharacter('Character'), self.toCharacterNode(scenePos))
            # elif itemType in [ItemType.COMMENT, ItemType.TOOL, ItemType.COST]:
            #     item = StickerItem(Node(scenePos.x(), scenePos.y()), itemType)
            # else:
            #     item = EventItem(self.toEventNode(scenePos), itemType)

            self.addItem(item)
            self.itemAdded.emit(itemType, item)
        self.endAdditionMode()
