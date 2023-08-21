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
from typing import Any, Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent, QPen, QPainterPath, QColor
from PyQt6.QtWidgets import QGraphicsView, QAbstractGraphicsShapeItem, QGraphicsItem, QGraphicsPathItem
from overrides import overrides

from src.main.python.plotlyst.core.domain import Node


class ConnectorItem(QGraphicsPathItem):

    def __init__(self, source: QAbstractGraphicsShapeItem, target: QAbstractGraphicsShapeItem,
                 pen: Optional[QPen] = None):
        super(ConnectorItem, self).__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self._source = source
        self._target = target
        if pen:
            self.setPen(pen)
        else:
            self.setPen(QPen(QColor(Qt.GlobalColor.darkBlue), 2))

        self.rearrange()

    def rearrange(self):
        self.setPos(self._source.sceneBoundingRect().center())

        path = QPainterPath()
        target_x = self._target.scenePos().x() - self.pos().x()
        target_y = self._target.scenePos().y()
        path.quadTo(0, target_y / 2, target_x, target_y - self._source.scenePos().y())
        # if self._target.scenePos().y() < 0:
        # elif self._target.scenePos().y() > 0:
        #     path.quadTo(0, target_y / 2, target_x, target_y)
        # else:
        #     path.lineTo(target_x, target_y)

        self.setPath(path)

    def source(self) -> QAbstractGraphicsShapeItem:
        return self._source

    def target(self) -> QAbstractGraphicsShapeItem:
        return self._target


class NodeItem(QAbstractGraphicsShapeItem):
    def __init__(self, node: Node, parent=None):
        super().__init__(parent)
        self._node = node

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._posChangedTimer = QTimer()
        self._posChangedTimer.setInterval(1000)
        self._posChangedTimer.timeout.connect(self._posChangedOnTimeout)

    @overrides
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._posChangedTimer.start(1000)
            self._onPosChanged()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._onSelection(value)
        return super(NodeItem, self).itemChange(change, value)

    def _onPosChanged(self):
        pass

    def _onSelection(self, selected: bool):
        pass

    def _posChangedOnTimeout(self):
        self._posChangedTimer.stop()
        self._node.x = self.scenePos().x()
        self._node.y = self.scenePos().y()


class BaseGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(BaseGraphicsView, self).__init__(parent)
        self._moveOriginX = 0
        self._moveOriginY = 0
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()
        super(BaseGraphicsView, self).mousePressEvent(event)

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.itemAt(
                event.pos()) and (
                event.buttons() & Qt.MouseButton.MiddleButton or event.buttons() & Qt.MouseButton.RightButton):
            oldPoint = self.mapToScene(self._moveOriginX, self._moveOriginY)
            newPoint = self.mapToScene(event.pos())
            translation = newPoint - oldPoint
            self.translate(translation.x(), translation.y())

            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()
        super(BaseGraphicsView, self).mouseMoveEvent(event)

    @overrides
    def wheelEvent(self, event: QWheelEvent) -> None:
        super(BaseGraphicsView, self).wheelEvent(event)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            diff = event.angleDelta().y()
            scale = diff / 1200
            self.scale(1 + scale, 1 + scale)
