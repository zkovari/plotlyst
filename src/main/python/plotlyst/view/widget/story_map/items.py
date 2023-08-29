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
from enum import Enum
from typing import Optional, List

from PyQt6.QtCore import Qt, pyqtSignal, QRect, QRectF, QPoint, QPointF, QTimer
from PyQt6.QtGui import QIcon, QColor, QPainter, QPen, QFontMetrics
from PyQt6.QtWidgets import QWidget, QApplication, QAbstractGraphicsShapeItem, QStyleOptionGraphicsItem, \
    QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QGraphicsRectItem, QGraphicsItem
from overrides import overrides

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Character, Node
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.graphics import NodeItem, AbstractSocketItem


def draw_rect(painter: QPainter, item: QAbstractGraphicsShapeItem):
    painter.setPen(QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine))
    painter.drawRoundedRect(item.boundingRect(), 2, 2)


def draw_center(painter: QPainter, item: QAbstractGraphicsShapeItem):
    painter.setPen(QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine))
    painter.drawEllipse(item.boundingRect().center(), 1, 1)


def draw_zero(painter: QPainter):
    painter.setPen(QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DashLine))
    painter.drawEllipse(QPointF(0, 0), 1, 1)


def draw_helpers(painter: QPainter, item: QAbstractGraphicsShapeItem):
    draw_rect(painter, item)
    draw_center(painter, item)
    draw_zero(painter)


def v_center(ref_height: int, item_height: int) -> int:
    return (ref_height - item_height) // 2


class ItemType(Enum):
    EVENT = 1
    CHARACTER = 2
    GOAL = 3
    CONFLICT = 4
    DISTURBANCE = 5
    BACKSTORY = 6
    SETUP = 7
    QUESTION = 8
    FORESHADOWING = 9
    COMMENT = 10
    TOOL = 11
    COST = 12


class MindMapNode(NodeItem):
    def mindMapScene(self) -> 'EventsMindMapScene':
        return self.scene()

    def linkMode(self) -> bool:
        return self.mindMapScene().linkMode()


class SocketItem(AbstractSocketItem):
    def __init__(self, orientation: Qt.Edge, parent: 'ConnectableNode'):
        super().__init__(orientation, parent)

        self._size = 16
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self._linkAvailable = True
        self.setToolTip('Connect')

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        if self._linkAvailable:
            painter.setPen(QPen(QColor(PLOTLYST_SECONDARY_COLOR), 2))
        else:
            painter.setPen(QPen(QColor('lightgrey'), 2))

        radius = 7 if self._hovered else 5
        painter.drawEllipse(QPointF(self._size / 2, self._size // 2), radius, radius)
        if self._hovered and self.mindMapScene().linkMode():
            painter.drawEllipse(QPointF(self._size / 2, self._size // 2), 2, 2)

    @overrides
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = True
        if self.mindMapScene().linkMode() and self.mindMapScene().linkSource().parentItem() == self.parentItem():
            self._linkAvailable = False
        else:
            self._linkAvailable = True
        self.setToolTip('Connect' if self._linkAvailable else 'Cannot connect to itself')
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = False
        self._linkAvailable = True
        self.setToolTip('Connect')
        self.update()

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    @overrides
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.mindMapScene().linkMode():
            if self.mindMapScene().linkSource().parentItem() != self.parentItem():
                self.mindMapScene().link(self)
        else:
            self.mindMapScene().startLink(self)

    def mindMapScene(self) -> 'EventsMindMapScene':
        return self.scene()


class SelectorRectItem(QGraphicsRectItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._startingPoint: QPointF = QPointF(0, 0)
        self._rect = QRectF()

        self.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DashLine))

    def start(self, pos: QPointF):
        self._startingPoint = pos
        self._rect.setTopLeft(pos)
        self.setRect(self._rect)

    def adjust(self, pos: QPointF):
        x1 = min(self._startingPoint.x(), pos.x())
        y1 = min(self._startingPoint.y(), pos.y())
        x2 = max(self._startingPoint.x(), pos.x())
        y2 = max(self._startingPoint.y(), pos.y())

        self._rect.setTopLeft(QPointF(x1, y1))
        self._rect.setBottomRight(QPointF(x2, y2))

        self.setRect(self._rect)


class PlaceholderItem(SocketItem):
    def __init__(self, parent=None):
        super().__init__(Qt.Edge.RightEdge, parent)
        self.setEnabled(False)
        self.setAcceptHoverEvents(False)
        self.setToolTip('Click to add a new node')


class StickerItem(MindMapNode):
    displayMessage = pyqtSignal()

    def __init__(self, node: Node, type: ItemType, parent=None):
        super().__init__(node, parent)
        self._size = 28
        if type == ItemType.COMMENT:
            self._icon = IconRegistry.from_name('mdi.comment-text', PLOTLYST_SECONDARY_COLOR)
        elif type == ItemType.TOOL:
            self._icon = IconRegistry.tool_icon()
        if type == ItemType.COST:
            self._icon = IconRegistry.cost_icon()

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(RELAXED_WHITE_COLOR))
        painter.drawRect(3, 3, self._size - 6, self._size - 10)
        self._icon.paint(painter, 0, 0, self._size, self._size)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self.mindMapScene().displayStickerMessage(self)

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        QTimer.singleShot(300, self.mindMapScene().hideStickerMessage)

    @overrides
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.mindMapScene().hideStickerMessage()


class ConnectableNode(MindMapNode):
    def __init__(self, node: Node, parent=None):
        super().__init__(node, parent)
        self._sockets: List[SocketItem] = []

    def removeConnectors(self):
        for socket in self._sockets:
            socket.removeConnectors()

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.linkMode() or event.modifiers() & Qt.KeyboardModifier.AltModifier:
            self._setSocketsVisible()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if not self.isSelected():
            self._setSocketsVisible(False)

    @overrides
    def _onPosChanged(self):
        for socket in self._sockets:
            socket.rearrangeConnectors()

    @overrides
    def _onSelection(self, selected: bool):
        self._setSocketsVisible(selected)

    def _setSocketsVisible(self, visible: bool = True):
        for socket in self._sockets:
            socket.setVisible(visible)


class EventItem(ConnectableNode):
    Margin: int = 30
    Padding: int = 20

    def __init__(self, node: Node, itemType: ItemType, parent=None):
        super().__init__(node, parent)
        self._text: str = 'New event'
        self._itemType = itemType
        self._icon: Optional[QIcon] = None
        self._iconSize: int = 0
        self._iconTextSpacing: int = 3
        if itemType == ItemType.GOAL:
            self._icon = IconRegistry.goal_icon()
        elif itemType == ItemType.CONFLICT:
            self._icon = IconRegistry.conflict_icon()
        elif itemType == ItemType.BACKSTORY:
            self._icon = IconRegistry.backstory_icon()
        elif itemType == ItemType.DISTURBANCE:
            self._icon = IconRegistry.inciting_incident_icon()
        elif itemType == ItemType.QUESTION:
            self._icon = IconRegistry.from_name('ei.question-sign')
        elif itemType == ItemType.SETUP:
            self._icon = IconRegistry.from_name('ri.seedling-fill')
        elif itemType == ItemType.FORESHADOWING:
            self._icon = IconRegistry.from_name('mdi6.crystal-ball')

        self._font = QApplication.font()
        # self._font.setPointSize(16)
        self._metrics = QFontMetrics(self._font)
        self._textRect: QRect = QRect(0, 0, 1, 1)
        self._width = 1
        self._height = 1
        self._nestedRectWidth = 1
        self._nestedRectHeight = 1

        self._socketLeft = SocketItem(Qt.Edge.LeftEdge, self)
        self._socketTopLeft = SocketItem(Qt.Edge.TopEdge, self)
        self._socketTopCenter = SocketItem(Qt.Edge.TopEdge, self)
        self._socketTopRight = SocketItem(Qt.Edge.TopEdge, self)
        self._socketRight = SocketItem(Qt.Edge.RightEdge, self)
        self._socketBottomLeft = SocketItem(Qt.Edge.BottomEdge, self)
        self._socketBottomCenter = SocketItem(Qt.Edge.BottomEdge, self)
        self._socketBottomRight = SocketItem(Qt.Edge.BottomEdge, self)
        self._sockets.extend([self._socketLeft,
                              self._socketTopLeft, self._socketTopCenter, self._socketTopRight,
                              self._socketRight,
                              self._socketBottomRight, self._socketBottomCenter, self._socketBottomLeft])
        self._setSocketsVisible(False)

        self._recalculateRect()

    def text(self) -> str:
        return self._text

    def setText(self, text: str):
        self._text = text
        self._recalculateRect()
        self.prepareGeometryChange()
        self.setSelected(False)
        self.update()

    def textRect(self) -> QRect:
        return self._textRect

    def textSceneRect(self) -> QRectF:
        return self.mapRectToScene(self._textRect.toRectF())

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self.Margin, self.Margin, self._nestedRectWidth, self._nestedRectHeight, 2, 2)

        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setFont(self._font)
        painter.drawText(self._textRect, Qt.AlignmentFlag.AlignCenter, self._text)
        painter.drawRoundedRect(self.Margin, self.Margin, self._nestedRectWidth, self._nestedRectHeight, 24, 24)

        if self._icon:
            self._icon.paint(painter, self.Margin + self.Padding - self._iconTextSpacing,
                             self.Margin + v_center(self.Padding * 2 + self._textRect.height(), self._iconSize),
                             self._iconSize, self._iconSize)

    @overrides
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.mindMapScene().editEventText(self)

    def _recalculateRect(self):
        self._textRect = self._metrics.boundingRect(self._text)
        self._iconSize = int(self._textRect.height() * 1.25) if self._icon else 0
        self._textRect.moveTopLeft(QPoint(self.Margin + self.Padding, self.Margin + self.Padding))
        self._textRect.moveTopLeft(QPoint(self._textRect.x() + self._iconSize, self._textRect.y()))

        self._width = self._textRect.width() + self._iconSize + self.Margin * 2 + self.Padding * 2
        self._height = self._textRect.height() + self.Margin * 2 + self.Padding * 2

        self._nestedRectWidth = self._textRect.width() + self.Padding * 2 + self._iconSize
        self._nestedRectHeight = self._textRect.height() + self.Padding * 2

        socketWidth = self._socketLeft.boundingRect().width()
        socketRad = socketWidth / 2
        socketPadding = (self.Margin - socketWidth) / 2
        self._socketTopCenter.setPos(self._width / 2 - socketRad, socketPadding)
        self._socketTopLeft.setPos(self._nestedRectWidth / 3 - socketRad, socketPadding)
        self._socketTopRight.setPos(self._nestedRectWidth, socketPadding)
        self._socketRight.setPos(self._width - self.Margin + socketPadding, self._height / 2 - socketRad)
        self._socketBottomCenter.setPos(self._width / 2 - socketRad, self._height - self.Margin + socketPadding)
        self._socketBottomLeft.setPos(self._nestedRectWidth / 3 - socketRad,
                                      self._height - self.Margin + socketPadding)
        self._socketBottomRight.setPos(self._nestedRectWidth, self._height - self.Margin + socketPadding)
        self._socketLeft.setPos(socketPadding, self._height / 2 - socketRad)


class CharacterItem(ConnectableNode):
    Margin: int = 25

    def __init__(self, node: Node, character: Optional[Character], parent=None):
        super().__init__(node, parent)
        self._character: Optional[Character] = character
        self._size: int = 68

        self._socketTop = SocketItem(Qt.Edge.TopEdge, self)
        self._socketRight = SocketItem(Qt.Edge.RightEdge, self)
        self._socketBottom = SocketItem(Qt.Edge.BottomEdge, self)
        self._socketLeft = SocketItem(Qt.Edge.LeftEdge, self)
        self._sockets.extend([self._socketLeft, self._socketTop, self._socketRight, self._socketBottom])
        socketSize = self._socketTop.boundingRect().width()
        half = self.Margin + v_center(self._size, socketSize)
        padding = v_center(self.Margin, socketSize)
        self._socketTop.setPos(half, padding)
        self._socketRight.setPos(self._size + self.Margin + padding, half)
        self._socketBottom.setPos(half, self._size + self.Margin + padding)
        self._socketLeft.setPos(padding, half)

        self._setSocketsVisible(False)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size + self.Margin * 2, self._size + self.Margin * 2)

    def setCharacter(self, character: Character):
        self._character = character
        self.update()

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self.Margin, self.Margin, self._size, self._size, 2, 2)

        if self._character is None:
            avatar = IconRegistry.character_icon()
        else:
            avatar = avatars.avatar(self._character)
        avatar.paint(painter, self.Margin, self.Margin, self._size, self._size)