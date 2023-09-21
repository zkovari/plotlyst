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
from typing import Any, Optional, List

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QColor, QIcon, QPolygonF
from PyQt6.QtWidgets import QAbstractGraphicsShapeItem, QGraphicsItem, QGraphicsPathItem, QGraphicsSceneMouseEvent, \
    QStyleOptionGraphicsItem, QWidget, \
    QGraphicsRectItem, QGraphicsSceneHoverEvent, QGraphicsPolygonItem
from overrides import overrides

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Node, Relation, Connector
from src.main.python.plotlyst.view.icons import IconRegistry


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

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = False
        self._linkAvailable = True
        self.setToolTip('Connect')
        self.prepareGeometryChange()
        self.update()

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


class PlaceholderSocketItem(AbstractSocketItem):
    def __init__(self, parent=None):
        super().__init__(0, parent=parent)
        self.setEnabled(False)
        self.setAcceptHoverEvents(False)

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        pass


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

        path = QPainterPath()

        start = self.scenePos()
        end = self._target.sceneBoundingRect().center()

        width = end.x() - start.x()
        height = end.y() - start.y()

        angle = math.degrees(math.atan2(-height / 2, width))
        if abs(height) < 5:
            line = True
            path.lineTo(width, height)
        else:
            line = False
            if self._source.angle() >= 0:
                path.quadTo(0, height / 2, width, height)
            else:
                path.quadTo(width / 2, -height / 2, width, height)
                angle = math.degrees(math.atan2(-height / 2, width / 2))

        self._arrowheadItem.setPos(width, height)
        self._arrowheadItem.setRotation(-angle)

        if self._icon:
            if line:
                point = path.pointAtPercent(0.4)
            else:
                point = path.pointAtPercent(0.6)
            self._iconBadge.setPos(point.x() - self._iconBadge.boundingRect().width() / 2,
                                   point.y() - self._iconBadge.boundingRect().height() / 2)

        # if line:
        #     point = path.pointAtPercent(0.4)
        # else:
        #     point = path.pointAtPercent(0.6)
        # path.addText(point, QApplication.font(), 'Romance')
        self.setPath(path)

    def source(self) -> AbstractSocketItem:
        return self._source

    def target(self) -> AbstractSocketItem:
        return self._target

    def _setColor(self, color: QColor):
        self._color = color
        pen = self.pen()
        pen.setColor(self._color)
        self.setPen(pen)

        arrowPen = self._arrowheadItem.pen()
        arrowPen.setColor(self._color)
        self._arrowheadItem.setPen(arrowPen)
        self._arrowheadItem.setBrush(self._color)


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
            self._posChangedTimer.start(1000)
            self._onPosChanged()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._onSelection(value)
        return super(NodeItem, self).itemChange(change, value)

    @abstractmethod
    def socket(self, angle: float) -> AbstractSocketItem:
        pass

    def _onPosChanged(self):
        for socket in self._sockets:
            socket.rearrangeConnectors()

    def _onSelection(self, selected: bool):
        pass

    def _posChangedOnTimeout(self):
        self._posChangedTimer.stop()
        self._node.x = self.scenePos().x()
        self._node.y = self.scenePos().y()
        self.networkScene().itemChangedEvent(self)
