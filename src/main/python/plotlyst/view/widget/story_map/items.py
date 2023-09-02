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

from PyQt6.QtCore import Qt, pyqtSignal, QRect, QRectF, QPoint, QPointF, QTimer
from PyQt6.QtGui import QIcon, QColor, QPainter, QPen, QFontMetrics
from PyQt6.QtWidgets import QWidget, QApplication, QStyleOptionGraphicsItem, \
    QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QGraphicsItem
from overrides import overrides

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Character, Node
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.graphics import NodeItem, AbstractSocketItem, NetworkItemType


def v_center(ref_height: int, item_height: int) -> int:
    return (ref_height - item_height) // 2


class ItemType(NetworkItemType):
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

    def mindMapScene(self) -> 'EventsMindMapScene':
        return self.scene()


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

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.linkMode() or event.modifiers() & Qt.KeyboardModifier.AltModifier:
            self._setSocketsVisible()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if not self.isSelected():
            self._setSocketsVisible(False)

    @overrides
    def _onSelection(self, selected: bool):
        super()._onSelection(selected)
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
        self._updateIcon()

        self._font = QApplication.font()
        self._metrics = QFontMetrics(self._font)
        self._textRect: QRect = QRect(0, 0, 1, 1)
        self._width = 1
        self._height = 1
        self._nestedRectWidth = 1
        self._nestedRectHeight = 1

        self._socketLeft = SocketItem(180, parent=self)
        self._socketTopLeft = SocketItem(135, parent=self)
        self._socketTopCenter = SocketItem(90, parent=self)
        self._socketTopRight = SocketItem(45, parent=self)
        self._socketRight = SocketItem(0, parent=self)
        self._socketBottomLeft = SocketItem(-135, parent=self)
        self._socketBottomCenter = SocketItem(-90, parent=self)
        self._socketBottomRight = SocketItem(-45, parent=self)
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
        self.setSelected(False)
        self._refresh()

    def itemType(self) -> ItemType:
        return self._itemType

    def setIcon(self, icon: QIcon):
        self._icon = icon
        self._refresh()

    def setFontSettings(self, size: Optional[int] = None, bold: Optional[bool] = None, italic: Optional[bool] = None,
                        underline: Optional[bool] = None):
        if size is not None:
            self._font.setPointSize(size)
        if bold is not None:
            self._font.setBold(bold)
        if italic is not None:
            self._font.setItalic(italic)
        if underline is not None:
            self._font.setUnderline(underline)

        self._metrics = QFontMetrics(self._font)

        self._refresh()

    def setItemType(self, itemType: ItemType):
        self._itemType = itemType
        self._updateIcon()

        self._refresh()

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
        painter.setBrush(QColor(RELAXED_WHITE_COLOR))
        painter.drawRoundedRect(self.Margin, self.Margin, self._nestedRectWidth, self._nestedRectHeight, 24, 24)
        painter.setFont(self._font)
        painter.drawText(self._textRect, Qt.AlignmentFlag.AlignCenter, self._text)

        if self._icon:
            self._icon.paint(painter, self.Margin + self.Padding - self._iconTextSpacing,
                             self.Margin + v_center(self.Padding * 2 + self._textRect.height(), self._iconSize),
                             self._iconSize, self._iconSize)

    @overrides
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.mindMapScene().editEventText(self)

    @overrides
    def _onSelection(self, selected: bool):
        super()._onSelection(selected)
        if selected:
            self.mindMapScene().showEditor(self)
        else:
            self.mindMapScene().hideEditor()

    @overrides
    def _onPosChanged(self):
        super()._onPosChanged()
        if self.isSelected():
            self.mindMapScene().hideEditor()

    def _refresh(self):
        self._recalculateRect()
        self.prepareGeometryChange()
        self.update()

    def _updateIcon(self):
        if self._itemType == ItemType.GOAL:
            self._icon = IconRegistry.goal_icon()
        elif self._itemType == ItemType.CONFLICT:
            self._icon = IconRegistry.conflict_icon()
        elif self._itemType == ItemType.BACKSTORY:
            self._icon = IconRegistry.backstory_icon()
        elif self._itemType == ItemType.DISTURBANCE:
            self._icon = IconRegistry.inciting_incident_icon()
        elif self._itemType == ItemType.QUESTION:
            self._icon = IconRegistry.from_name('ei.question-sign')
        elif self._itemType == ItemType.SETUP:
            self._icon = IconRegistry.from_name('ri.seedling-fill')
        elif self._itemType == ItemType.FORESHADOWING:
            self._icon = IconRegistry.from_name('mdi6.crystal-ball')

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

        self._socketTop = SocketItem(90, parent=self)
        self._socketRight = SocketItem(0, parent=self)
        self._socketBottom = SocketItem(-90, parent=self)
        self._socketLeft = SocketItem(180, parent=self)
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
