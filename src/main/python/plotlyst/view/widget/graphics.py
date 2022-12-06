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

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent
from PyQt6.QtWidgets import QGraphicsView
from overrides import overrides


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
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.LeftButton:
            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()
        super(BaseGraphicsView, self).mousePressEvent(event)

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.MiddleButton or event.buttons() & Qt.MouseButton.LeftButton:
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
