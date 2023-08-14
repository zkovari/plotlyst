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

from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QKeyEvent
from PyQt6.QtWidgets import QGraphicsScene, QWidget, QAbstractGraphicsShapeItem, QGraphicsSceneHoverEvent, \
    QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem
from overrides import overrides

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR, PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel, Character, CharacterNode
from src.main.python.plotlyst.view.icons import avatars
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView, NodeItem


def draw_rect(painter: QPainter, item: QAbstractGraphicsShapeItem):
    painter.setPen(QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine))
    painter.drawRoundedRect(item.boundingRect(), 2, 2)


class SocketItem(QAbstractGraphicsShapeItem):
    def __init__(self, parent):
        super(SocketItem, self).__init__(parent)
        self._parent = parent
        self._size = 16
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self.setToolTip('Link')

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        painter.setPen(QPen(QColor(PLOTLYST_SECONDARY_COLOR)))
        painter.setBrush(QColor(PLOTLYST_SECONDARY_COLOR))
        radius = 7 if self._hovered else 5
        painter.drawEllipse(QPointF(self._size / 2, self._size // 2), radius, radius)

    @overrides
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = True
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = False
        self.update()

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    def mindMapScene(self) -> 'EventsMindMapScene':
        return self.scene()

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.mindMapScene().startLink()


class CharacterItem(NodeItem):
    def __init__(self, character: Character, node: CharacterNode, parent=None):
        super().__init__(node, parent)
        self._character = character

        self._size: int = 108
        self._margin = 30

        self._socketTop = SocketItem(self)
        self._socketRight = SocketItem(self)
        self._socketBottom = SocketItem(self)
        self._socketLeft = SocketItem(self)
        self._sockets = [self._socketLeft, self._socketTop, self._socketRight, self._socketBottom]
        width = self._socketTop.boundingRect().width()
        half = self._margin + (self._size - width) / 2
        padding = (self._margin - width) / 2
        self._socketTop.setPos(half, padding)
        self._socketRight.setPos(self._size + self._margin + padding, half)
        self._socketBottom.setPos(half, self._size + self._margin + padding)
        self._socketLeft.setPos(padding, half)

        for socket in self._sockets:
            socket.setVisible(False)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size + self._margin * 2, self._size + self._margin * 2)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self._margin, self._margin, self._size, self._size, 2, 2)

        draw_rect(painter, self)

        avatar = avatars.avatar(self._character)
        avatar.paint(painter, self._margin, self._margin, self._size, self._size)

    def _onSelection(self, selected: bool):
        for socket in self._sockets:
            socket.setVisible(selected)


class EventsMindMapScene(QGraphicsScene):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._linkMode: bool = False

        item = CharacterItem(novel.characters[0], CharacterNode(50, 50))
        item.setPos(50, 50)
        self.addItem(item)

    def linkMode(self) -> bool:
        return self._linkMode

    def startLink(self):
        self._linkMode = True

    def endLink(self):
        self._linkMode = False

    @overrides
    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            print(event.scenePos())
        super().mouseMoveEvent(event)

    @overrides
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape and self.linkMode():
            self.endLink()


class EventsMindMapView(BaseGraphicsView):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene = EventsMindMapScene(self._novel)
        self.setScene(self._scene)
        self.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))

        self.scale(0.6, 0.6)
