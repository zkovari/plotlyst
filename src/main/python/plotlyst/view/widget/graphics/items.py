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
from abc import abstractmethod
from enum import Enum
from typing import Any, Optional, List

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QColor, QIcon, QPolygonF, QBrush, QFontMetrics
from PyQt6.QtWidgets import QAbstractGraphicsShapeItem, QGraphicsItem, QGraphicsPathItem, QGraphicsSceneMouseEvent, \
    QStyleOptionGraphicsItem, QWidget, \
    QGraphicsSceneHoverEvent, QGraphicsPolygonItem, QApplication
from overrides import overrides
from qthandy import pointy

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR, PLOTLYST_SECONDARY_COLOR, PLOTLYST_TERTIARY_COLOR
from src.main.python.plotlyst.core.domain import Node, Relation, Connector, Character, NODE_SUBTYPE_GOAL, \
    NODE_SUBTYPE_CONFLICT, NODE_SUBTYPE_BACKSTORY, NODE_SUBTYPE_DISTURBANCE, NODE_SUBTYPE_QUESTION, \
    NODE_SUBTYPE_FORESHADOWING, DiagramNodeType
from src.main.python.plotlyst.view.icons import IconRegistry, avatars


def v_center(ref_height: int, item_height: int) -> int:
    return (ref_height - item_height) // 2


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


def alt_modifier(event: QGraphicsSceneHoverEvent) -> bool:
    return event.modifiers() & Qt.KeyboardModifier.AltModifier


class IconBadge(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._size: int = 32
        self._icon: Optional[QIcon] = None
        self._color: QColor = QColor('black')

    def setIcon(self, icon: QIcon, borderColor: Optional[QColor] = None):
        self._icon = icon
        if borderColor:
            self._color = borderColor
        self.update()

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QPen(self._color, 2))
        painter.setBrush(QColor(RELAXED_WHITE_COLOR))
        painter.drawEllipse(0, 0, self._size, self._size)

        if self._icon:
            self._icon.paint(painter, 3, 3, self._size - 5, self._size - 5)


class AbstractSocketItem(QAbstractGraphicsShapeItem):
    def __init__(self, angle: float, size: int = 16, parent=None):
        super().__init__(parent)
        self._size = size
        self._angle: float = angle
        self._hovered = False
        self._linkAvailable = True

        self.setToolTip('Connect')
        self.setAcceptHoverEvents(True)

        self._connectors: List[ConnectorItem] = []

    def angle(self) -> float:
        return self._angle

    def setAngle(self, angle: float):
        self._angle = angle

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = True
        if self.networkScene().linkMode() and self.networkScene().linkSource().parentItem() == self.parentItem():
            self._linkAvailable = False
        else:
            self._linkAvailable = True
        self.setToolTip('Connect' if self._linkAvailable else 'Cannot connect to itself')
        self.prepareGeometryChange()
        self.update()

        for connector in self._connectors:
            connector.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = False
        self._linkAvailable = True
        self.setToolTip('Connect')
        self.prepareGeometryChange()
        self.update()

        for connector in self._connectors:
            connector.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    @overrides
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.networkScene().linkMode():
            if self.networkScene().linkSource().parentItem() != self.parentItem():
                self.networkScene().link(self)
        else:
            self.networkScene().startLink(self)

    def connectors(self) -> List['ConnectorItem']:
        return self._connectors

    def addConnector(self, connector: 'ConnectorItem'):
        self._connectors.append(connector)

    def rearrangeConnectors(self):
        for con in self._connectors:
            con.rearrange()

    def removeConnectors(self):
        self._connectors.clear()

    def removeConnector(self, connector: 'ConnectorItem'):
        self._connectors.remove(connector)

    def networkScene(self) -> 'NetworkScene':
        return self.scene()


class FilledSocketItem(AbstractSocketItem):
    Size: int = 20

    def __init__(self, angle: float, parent=None):
        super().__init__(angle, self.Size, parent)
        pointy(self)

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        color = PLOTLYST_SECONDARY_COLOR if self._hovered else PLOTLYST_TERTIARY_COLOR
        painter.setPen(QPen(QColor(color), 1))
        painter.setBrush(QColor(color))

        radius = self.Size // 2
        painter.drawEllipse(QPointF(self.Size / 2, self.Size // 2), radius, radius)


class DotCircleSocketItem(AbstractSocketItem):

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        if self._linkAvailable:
            painter.setPen(QPen(QColor(PLOTLYST_SECONDARY_COLOR), 2))
        else:
            painter.setPen(QPen(QColor('lightgrey'), 2))

        radius = 7 if self._hovered else 5
        painter.drawEllipse(QPointF(self._size / 2, self._size // 2), radius, radius)
        if self._hovered and self.networkScene().linkMode():
            painter.drawEllipse(QPointF(self._size / 2, self._size // 2), 2, 2)


class PlaceholderSocketItem(AbstractSocketItem):
    def __init__(self, parent=None):
        super().__init__(0, parent=parent)
        self.setEnabled(False)
        self.setAcceptHoverEvents(False)

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        pass


class ConnectorType(Enum):
    Linear = 0
    Curved = 1


class ConnectorItem(QGraphicsPathItem):

    def __init__(self, source: AbstractSocketItem, target: AbstractSocketItem,
                 pen: Optional[QPen] = None):
        super(ConnectorItem, self).__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self._source = source
        self._target = target
        self._connector: Optional[Connector] = None
        self._color: QColor = QColor('darkblue')
        self._relation: Optional[Relation] = None
        self._icon: Optional[str] = None
        self._defaultLineType: ConnectorType = ConnectorType.Curved
        self._line: bool = True if self._defaultLineType == ConnectorType.Linear else False
        if pen:
            self.setPen(pen)
        else:
            self.setPen(QPen(self._color, 2))

        self._arrowhead = QPolygonF([
            QPointF(0, -5),
            QPointF(10, 0),
            QPointF(0, 5),
        ])
        self._arrowheadItem = QGraphicsPolygonItem(self._arrowhead, self)
        self._arrowheadItem.setPen(QPen(self._color, 1))
        self._arrowheadItem.setBrush(self._color)

        self._iconBadge = IconBadge(self)
        self._iconBadge.setVisible(False)

        self.rearrange()

    def networkScene(self) -> 'NetworkScene':
        return self.scene()

    def source(self) -> AbstractSocketItem:
        return self._source

    def target(self) -> AbstractSocketItem:
        return self._target

    def connector(self) -> Optional[Connector]:
        return self._connector

    def setConnector(self, connector: Connector):
        self._connector = None
        self.setPenStyle(connector.pen)
        self.setPenWidth(connector.width)
        self.setColor(QColor(connector.color))
        if connector.icon:
            self.setIcon(connector.icon)
        self._connector = connector

    def penStyle(self) -> Qt.PenStyle:
        return self.pen().style()

    def setPenStyle(self, penStyle: Qt.PenStyle):
        pen = self.pen()
        pen.setStyle(penStyle)
        self.setPen(pen)
        self.update()
        if self._connector:
            self._connector.pen = penStyle
            self.networkScene().connectorChangedEvent(self)

    def penWidth(self) -> int:
        return self.pen().width()

    def setPenWidth(self, width: int):
        pen = self.pen()
        pen.setWidth(width)
        self.setPen(pen)

        arrowPen = self._arrowheadItem.pen()
        prevWidth = arrowPen.width()
        self._arrowheadItem.setScale(1.0 + (width - prevWidth) / 10)

        self.rearrange()
        if self._connector:
            self._connector.width = width
            self.networkScene().connectorChangedEvent(self)

    def relation(self) -> Optional[Relation]:
        return self._relation

    def setRelation(self, relation: Relation):
        self._icon = relation.icon

        self._setColor(QColor(relation.icon_color))

        self._relation = relation
        self._iconBadge.setIcon(IconRegistry.from_name(relation.icon, relation.icon_color), self._color)
        self._iconBadge.setVisible(True)

        self.rearrange()

        if self._connector:
            self._connector.type = relation.text
            self._connector.icon = relation.icon
            self._connector.color = relation.icon_color
            self.networkScene().connectorChangedEvent(self)

    def icon(self) -> Optional[str]:
        return self._icon

    def setIcon(self, icon: str, color: Optional[QColor] = None):
        self._icon = icon
        if color:
            self._color = color
        self._iconBadge.setIcon(IconRegistry.from_name(self._icon, self._color.name()), self._color)
        self._iconBadge.setVisible(True)
        self.rearrange()

        if self._connector:
            self._connector.icon = icon
            self.networkScene().connectorChangedEvent(self)

    def color(self) -> QColor:
        return self._color

    def setColor(self, color: QColor):
        self._setColor(color)
        if self._icon:
            self._iconBadge.setIcon(IconRegistry.from_name(self._icon, self._color.name()), self._color)

        self.update()

        if self._connector:
            self._connector.color = color.name()
            self.networkScene().connectorChangedEvent(self)

    def rearrange(self):
        self.setPos(self._source.sceneBoundingRect().center())

        start: QPointF = self.scenePos()
        end: QPointF = self._target.sceneBoundingRect().center()
        width: float = end.x() - start.x()
        height: float = end.y() - start.y()
        endPoint: QPointF = QPointF(width, height)
        endArrowAngle = math.degrees(math.atan2(-height / 2, width))

        if self._defaultLineType != ConnectorType.Linear and self._inProximity(width, height):
            self._line = True
        else:
            self._line = False

        path = QPainterPath()
        if self._line:
            self._rearrangeLinearConnector(path, width, height, endArrowAngle)
        else:
            self._rearrangeCurvedConnector(path, width, height, endArrowAngle, endPoint)

        self._arrowheadItem.setPos(width, height)
        self._rearrangeIcon(path)
        self._rearrangeText(path)

        self.setPath(path)

    def _rearrangeLinearConnector(self, path: QPainterPath, width: float, height: float, endArrowAngle: float):
        path.lineTo(width, height)
        self._arrowheadItem.setRotation(-endArrowAngle)

    def _rearrangeCurvedConnector(self, path: QPainterPath, width: float, height: float, endArrowAngle: float,
                                  endPoint: QPointF):
        if self._source.angle() >= 0:
            controlPoint = QPointF(0, height / 2)
        else:
            controlPoint = QPointF(width / 2, -height / 2)
            endArrowAngle = math.degrees(math.atan2(-height / 2, width / 2))
        path.quadTo(controlPoint, endPoint)
        self._arrowheadItem.setRotation(-endArrowAngle)

    def _rearrangeIcon(self, path: QPainterPath):
        if self._icon:
            if self._line:
                point = path.pointAtPercent(0.4)
            else:
                point = path.pointAtPercent(0.6)
            self._iconBadge.setPos(point.x() - self._iconBadge.boundingRect().width() / 2,
                                   point.y() - self._iconBadge.boundingRect().height() / 2)

    def _rearrangeText(self, path: QPainterPath):
        pass
        # if line:
        #     point = path.pointAtPercent(0.4)
        # else:
        #     point = path.pointAtPercent(0.6)
        # path.addText(point, QApplication.font(), 'Romance')

    def _setColor(self, color: QColor):
        self._color = color
        pen = self.pen()
        pen.setColor(self._color)
        self.setPen(pen)

        arrowPen = self._arrowheadItem.pen()
        arrowPen.setColor(self._color)
        self._arrowheadItem.setPen(arrowPen)
        self._arrowheadItem.setBrush(self._color)

    def _inProximity(self, width: float, height: float) -> bool:
        return abs(height) < 5 or abs(width) < 100


class NodeItem(QAbstractGraphicsShapeItem):
    def __init__(self, node: Node, parent=None):
        super().__init__(parent)
        self._node = node

        self.setPos(node.x, node.y)
        self._sockets: List[AbstractSocketItem] = []

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._posChangedTimer = QTimer()
        self._posChangedTimer.setInterval(1000)
        self._posChangedTimer.timeout.connect(self._posChangedOnTimeout)

    def node(self) -> Node:
        return self._node

    def networkScene(self) -> 'NetworkScene':
        return self.scene()

    def connectors(self) -> List[ConnectorItem]:
        connectors = []
        for socket in self._sockets:
            connectors.extend(socket.connectors())

        return connectors

    def clearConnectors(self):
        for socket in self._sockets:
            socket.removeConnectors()

    @overrides
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._posChangedTimer.start()
            self._onPosChanged()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._onSelection(value)
        return super(NodeItem, self).itemChange(change, value)

    @abstractmethod
    def socket(self, angle: float) -> AbstractSocketItem:
        pass

    def rearrangeConnectors(self):
        for socket in self._sockets:
            socket.rearrangeConnectors()

    def _onPosChanged(self):
        self.rearrangeConnectors()
        self.networkScene().itemChangedEvent(self)

    def _onSelection(self, selected: bool):
        pass

    def _posChangedOnTimeout(self):
        self._posChangedTimer.stop()
        self._node.x = self.scenePos().x()
        self._node.y = self.scenePos().y()
        scene = self.networkScene()
        if scene:
            scene.nodeChangedEvent(self._node)


class CharacterItem(NodeItem):
    Margin: int = 20
    PenWidth: int = 2

    def __init__(self, character: Character, node: Node, parent=None):
        super(CharacterItem, self).__init__(node, parent)
        self._character = character
        self._size: int = 68
        self._center = QPointF(self.Margin + self._size / 2, self.Margin + self._size / 2)
        self._outerRadius = self._size // 2 + self.Margin // 2

        self._linkDisplayedMode: bool = False

        self._socket = FilledSocketItem(0, self)
        self._socket.setVisible(False)

    def character(self) -> Character:
        return self._character

    def setCharacter(self, character: Character):
        self._character = character
        self._node.set_character(self._character)
        self.update()
        self.networkScene().nodeChangedEvent(self._node)

    @overrides
    def socket(self, angle: float) -> AbstractSocketItem:
        angle_radians = math.radians(-angle)
        x = self._center.x() + self._outerRadius * math.cos(angle_radians) - FilledSocketItem.Size // 2
        y = self._center.y() + self._outerRadius * math.sin(angle_radians) - FilledSocketItem.Size // 2

        self._socket.setAngle(angle)
        self._socket.setPos(x, y)

        return self._socket

    def addSocket(self, socket: AbstractSocketItem):
        self._sockets.append(socket)
        socket.setVisible(False)
        self._socket = FilledSocketItem(socket.angle(), self)
        self._socket.setVisible(False)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size + self.Margin * 2, self._size + self.Margin * 2)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self._linkDisplayedMode:
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
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.networkScene().linkMode() or alt_modifier(event):
            self._setConnectionEnabled(True)
            self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self._linkDisplayedMode and not self.isSelected():
            self._setConnectionEnabled(False)
            self.update()

    @overrides
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.networkScene().editItemEvent(self)

    @overrides
    def hoverMoveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if not self._linkDisplayedMode and alt_modifier(event):
            self._setConnectionEnabled(True)
        if self._linkDisplayedMode:
            angle = math.degrees(math.atan2(
                event.pos().y() - self._center.y(), event.pos().x() - self._center.x()
            ))
            angle_radians = math.radians(angle)
            x = self._center.x() + self._outerRadius * math.cos(angle_radians) - FilledSocketItem.Size // 2
            y = self._center.y() + self._outerRadius * math.sin(angle_radians) - FilledSocketItem.Size // 2
            self.prepareGeometryChange()
            self._socket.setAngle(-angle)
            self._socket.setPos(x, y)

            self.update()

    @overrides
    def _onSelection(self, selected: bool):
        super()._onSelection(selected)
        self._setConnectionEnabled(selected)

    def _setConnectionEnabled(self, enabled: bool):
        self._linkDisplayedMode = enabled
        self._socket.setVisible(enabled)
        self.update()


class EventItem(NodeItem):
    Margin: int = 30
    Padding: int = 20

    def __init__(self, node: Node, parent=None):
        super().__init__(node, parent)
        self._placeholderText: str = 'New event'
        self._text: str = self._node.text if self._node.text else ''
        self._setTooltip()

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

        self._socketLeft = DotCircleSocketItem(180, parent=self)
        self._socketTopLeft = DotCircleSocketItem(135, parent=self)
        self._socketTopCenter = DotCircleSocketItem(90, parent=self)
        self._socketTopRight = DotCircleSocketItem(45, parent=self)
        self._socketRight = DotCircleSocketItem(0, parent=self)
        self._socketBottomLeft = DotCircleSocketItem(-135, parent=self)
        self._socketBottomCenter = DotCircleSocketItem(-90, parent=self)
        self._socketBottomRight = DotCircleSocketItem(-45, parent=self)
        self._sockets.extend([self._socketLeft,
                              self._socketTopLeft, self._socketTopCenter, self._socketTopRight,
                              self._socketRight,
                              self._socketBottomRight, self._socketBottomCenter, self._socketBottomLeft])
        self._setSocketsVisible(False)

        self._font.setPointSize(self._node.size)
        self._font.setBold(self._node.bold)
        self._font.setItalic(self._node.italic)
        self._font.setUnderline(self._node.underline)
        self._metrics = QFontMetrics(self._font)
        self._refresh()

        self._recalculateRect()

    def text(self) -> str:
        return self._text

    def setText(self, text: str):
        self._text = text
        self._node.text = text
        self._setTooltip()
        self.setSelected(False)
        self._refresh()
        self.networkScene().nodeChangedEvent(self._node)

    @overrides
    def socket(self, angle: float) -> AbstractSocketItem:
        if angle == 0:
            return self._socketRight
        elif angle == 45:
            return self._socketTopRight
        elif angle == 90:
            return self._socketTopCenter
        elif angle == 135:
            return self._socketTopLeft
        elif angle == 180:
            return self._socketLeft
        elif angle == -135:
            return self._socketBottomLeft
        elif angle == -90:
            return self._socketBottomCenter
        elif angle == -45:
            return self._socketBottomRight

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.networkScene().linkMode() or alt_modifier(event):
            self._setSocketsVisible()

    def hoverMoveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if not self.networkScene().linkMode() and alt_modifier(event):
            self._setSocketsVisible()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if not self.isSelected():
            self._setSocketsVisible(False)

    def setIcon(self, icon: QIcon):
        self._icon = icon
        self._refresh()
        if self._node:
            self.networkScene().nodeChangedEvent(self._node)

    def setFontSettings(self, size: Optional[int] = None, bold: Optional[bool] = None, italic: Optional[bool] = None,
                        underline: Optional[bool] = None):
        if size is not None:
            self._font.setPointSize(size)
            self._node.size = size
        if bold is not None:
            self._font.setBold(bold)
            self._node.bold = bold
        if italic is not None:
            self._font.setItalic(italic)
            self._node.italic = italic
        if underline is not None:
            self._font.setUnderline(underline)
            self._node.underline = underline

        self._metrics = QFontMetrics(self._font)
        self._refresh()
        self.networkScene().nodeChangedEvent(self._node)

    def fontSize(self) -> int:
        return self._font.pointSize()

    def bold(self) -> bool:
        return self._font.bold()

    def italic(self) -> bool:
        return self._font.italic()

    def underline(self) -> bool:
        return self._font.underline()

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
        painter.drawText(self._textRect, Qt.AlignmentFlag.AlignCenter,
                         self._text if self._text else self._placeholderText)

        if self._icon:
            self._icon.paint(painter, self.Margin + self.Padding - self._iconTextSpacing,
                             self.Margin + v_center(self.Padding * 2 + self._textRect.height(), self._iconSize),
                             self._iconSize, self._iconSize)

    @overrides
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.networkScene().editItemEvent(self)

    def _setTooltip(self):
        self.setToolTip(self._text if self._text else self._placeholderText)

    def _setSocketsVisible(self, visible: bool = True):
        for socket in self._sockets:
            socket.setVisible(visible)

    @overrides
    def _onSelection(self, selected: bool):
        super()._onSelection(selected)
        self._setSocketsVisible(selected)

    def _refresh(self):
        self._recalculateRect()
        self.prepareGeometryChange()
        self.update()
        self.rearrangeConnectors()

    def _updateIcon(self):
        if self._node.subtype == NODE_SUBTYPE_GOAL:
            self._icon = IconRegistry.goal_icon()
        elif self._node.subtype == NODE_SUBTYPE_CONFLICT:
            self._icon = IconRegistry.conflict_icon()
        elif self._node.subtype == NODE_SUBTYPE_BACKSTORY:
            self._icon = IconRegistry.backstory_icon()
        elif self._node.subtype == NODE_SUBTYPE_DISTURBANCE:
            self._icon = IconRegistry.inciting_incident_icon()
        elif self._node.subtype == NODE_SUBTYPE_QUESTION:
            self._icon = IconRegistry.from_name('ei.question-sign')
        elif self._node.subtype == DiagramNodeType.SETUP:
            self._icon = IconRegistry.from_name('ri.seedling-fill')
        elif self._node.subtype == NODE_SUBTYPE_FORESHADOWING:
            self._icon = IconRegistry.from_name('mdi6.crystal-ball')

    def _recalculateRect(self):
        self._textRect = self._metrics.boundingRect(self._text if self._text else self._placeholderText)
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
        self._socketTopRight.setPos(self._nestedRectWidth + socketRad, socketPadding)
        self._socketRight.setPos(self._width - self.Margin + socketPadding, self._height / 2 - socketRad)
        self._socketBottomCenter.setPos(self._width / 2 - socketRad, self._height - self.Margin + socketPadding)
        self._socketBottomLeft.setPos(self._nestedRectWidth / 3 - socketRad,
                                      self._height - self.Margin + socketPadding)
        self._socketBottomRight.setPos(self._nestedRectWidth + socketRad, self._height - self.Margin + socketPadding)
        self._socketLeft.setPos(socketPadding, self._height / 2 - socketRad)
