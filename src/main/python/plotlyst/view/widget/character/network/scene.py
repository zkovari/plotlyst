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
from PyQt6.QtWidgets import QWidget, QGraphicsScene, QStyleOptionGraphicsItem, QGraphicsSceneHoverEvent, \
    QGraphicsSceneMouseEvent
from overrides import overrides

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR, PLOTLYST_TERTIARY_COLOR
from src.main.python.plotlyst.core.domain import Character, Novel, RelationsNetwork, CharacterNode
from src.main.python.plotlyst.view.icons import avatars
from src.main.python.plotlyst.view.widget.graphics import NodeItem, draw_helpers, AbstractSocketItem


class SocketItem(AbstractSocketItem):
    def __init__(self, parent=None):
        super().__init__(Qt.Edge.TopEdge, parent)

        self._size = 10

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setPen(QPen(QColor(PLOTLYST_SECONDARY_COLOR), 2))
        painter.setBrush(QColor(PLOTLYST_SECONDARY_COLOR))

        radius = self._size // 2
        painter.drawEllipse(QPointF(self._size / 2, self._size // 2), radius, radius)


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

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size + self.Margin * 2, self._size + self.Margin * 2)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        draw_helpers(painter, self)
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

    # @overrides
    # def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
    #     if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
    #         self._posChangedTimer.start(1000)
    #     elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
    #         if value:
    #             self._plusItem.setVisible(True)
    #             self._animation = qtanim.fade_in(self._plusItem)
    #         else:
    #             self.relationsScene().endLink()
    #             self._plusItem.setVisible(False)
    #             self._plusItem.reset()
    #     return super(CharacterItem, self).itemChange(change, value)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.relationsScene().linkMode():
            self._linkMode = True
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.relationsScene().linkMode() and not self.isSelected():
            self._linkMode = False
            self.update()

    @overrides
    def hoverMoveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self._linkMode:
            angle = math.degrees(math.atan2(
                event.pos().y() - self._center.y(), event.pos().x() - self._center.x()
            ))
            angle_radians = math.radians(angle)
            # rad = self._size // 2 + self.Margin // 2
            x = self._center.x() + self._outerRadius * math.cos(angle_radians) - self.PenWidth * 2
            y = self._center.y() + self._outerRadius * math.sin(angle_radians) - self.PenWidth * 2

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


class RelationsEditorScene(QGraphicsScene):
    charactersChanged = pyqtSignal(RelationsNetwork)
    charactersLinked = pyqtSignal(CharacterItem)

    def __init__(self, novel: Novel, parent=None):
        super(RelationsEditorScene, self).__init__(parent)
        self._novel = novel
        self._network: Optional[RelationsNetwork] = None
        self._linkMode: bool = False

        node = CharacterNode(50, 50)
        if self._novel.characters:
            node.set_character(self._novel.characters[0])
            self.addItem(CharacterItem(self._novel.characters[0], node))

    def setNetwork(self, network: RelationsNetwork):
        self._network = network

    # @overrides
    # def dragEnterEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
    #     if event.mimeData().hasFormat(CHARACTER_AVATAR_MIME_TYPE):
    #         event.accept()
    #
    # @overrides
    # def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
    #     if event.mimeData().hasFormat(CHARACTER_AVATAR_MIME_TYPE):
    #         event.accept()

    # @overrides
    # def dropEvent(self, event: 'QGraphicsSceneDragDropEvent') -> None:
    #     if event.mimeData().hasFormat(CHARACTER_AVATAR_MIME_TYPE):
    #         event.accept()
    #
    #         character: Character = event.mimeData().reference()
    #         node = CharacterNode(event.scenePos().x(), event.scenePos().y())
    #         node.set_character(character)
    #         self._network.nodes.append(node)
    #
    #         item = CharacterItem(character, node)
    #         item.setPos(event.scenePos())
    #         self.addItem(item)
    #         self.charactersChanged.emit(self._network)

    @overrides
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            for item in self.selectedItems():
                if isinstance(item, CharacterItem):
                    self._network.nodes[:] = [node for node in self._network.nodes if
                                              node.character_id != item.character().id]
                    self.removeItem(item)
                    self.charactersChanged.emit(self._network)

    def linkMode(self) -> bool:
        return self._linkMode

    def startLink(self):
        self._linkMode = True

    def endLink(self):
        self._linkMode = False

    def link(self, item: CharacterItem):
        self.charactersLinked.emit(item)
