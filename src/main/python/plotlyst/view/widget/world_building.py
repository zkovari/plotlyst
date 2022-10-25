"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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

from PyQt6.QtCore import Qt, QRectF, QRect
from PyQt6.QtGui import QMouseEvent, QWheelEvent, QPainter, QColor, QPen, QFontMetrics, QFont
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QAbstractGraphicsShapeItem, QStyleOptionGraphicsItem, \
    QWidget
from overrides import overrides


class WorldBuildingItem(QAbstractGraphicsShapeItem):

    def __init__(self, parent=None):
        super(WorldBuildingItem, self).__init__(parent)
        self._text = 'My new world'
        self._font = QFont('Helvetica', 14)
        self._metrics = QFontMetrics(self._font)
        self._rect = QRect(0, 0, 1, 1)
        self._recalculateRect()

    def setText(self, text: str):
        self._text = text
        self._recalculateRect()
        self.update()

    def _recalculateRect(self):
        self._rect = self._metrics.boundingRect(self._text)
        self._rect.setX(self._rect.x() - 10)
        self._rect.setWidth(self._rect.width() + 10)
        self._rect.setY(self._rect.y() - 5)
        self._rect.setHeight(self._rect.height() + 10)

    @overrides
    def boundingRect(self):
        return QRectF(self._rect)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor('#219ebc'))
        pen = QPen(QColor('#219ebc'), 1)
        painter.setPen(pen)
        painter.drawRoundedRect(self._rect, 25, 25)

        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(self._font)
        painter.drawText(0, 0, self._text)
        painter.end()


class WorldBuildingEditor(QGraphicsView):
    def __init__(self, parent=None):
        super(WorldBuildingEditor, self).__init__(parent)
        self._moveOriginX = 0
        self._moveOriginY = 0

        self._scene = QGraphicsScene()

        item = WorldBuildingItem()
        self._scene.addItem(item)

        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.MiddleButton:
            oldPoint = self.mapToScene(self._moveOriginX, self._moveOriginY)
            newPoint = self.mapToScene(event.pos())
            translation = newPoint - oldPoint
            self.translate(translation.x(), translation.y())

            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()

    @overrides
    def wheelEvent(self, event: QWheelEvent) -> None:
        super(WorldBuildingEditor, self).wheelEvent(event)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            diff = event.angleDelta().y()
            scale = (diff // 120) / 10
            self.scale(1 + scale, 1 + scale)
