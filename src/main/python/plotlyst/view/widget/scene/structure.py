"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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

from PyQt6.QtCore import QRectF, QPointF
from PyQt6.QtGui import QColor, QResizeEvent, QPainter, QPen
from PyQt6.QtWidgets import QGraphicsScene, QAbstractGraphicsShapeItem, QWidget, QGraphicsItem
from overrides import overrides

from plotlyst.common import WHITE_COLOR, PLOTLYST_MAIN_COLOR, PLOTLYST_TERTIARY_COLOR
from plotlyst.core.domain import Novel
from plotlyst.view.common import spawn
from plotlyst.view.widget.graphics import BaseGraphicsView
from plotlyst.view.widget.graphics.editor import ZoomBar


class SceneBeatItem(QAbstractGraphicsShapeItem):
    OFFSET: int = 25

    def __init__(self, parent=None):
        super().__init__(parent)
        self._width = 200
        self._height = 75

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(QColor(PLOTLYST_MAIN_COLOR), 2))
            painter.setBrush(QColor(PLOTLYST_TERTIARY_COLOR))
        else:
            painter.setPen(QPen(QColor('black'), 1))
            painter.setBrush(QColor(WHITE_COLOR))

        painter.drawConvexPolygon([
            QPointF(0, 0),  # Top left point
            QPointF(self.OFFSET, self._height / 2),  # Center left point
            QPointF(0, self._height),  # Bottom left point
            QPointF(self._width - self.OFFSET, self._height),  # Bottom right point
            QPointF(self._width, self._height / 2),  # Center right point with offset
            QPointF(self._width - self.OFFSET, 0)  # Top right point
        ])

        # painter.setFont(self._font)
        # painter.drawText(self._textRect, Qt.AlignmentFlag.AlignCenter,
        #                  self._text if self._text else self._placeholderText)


class SceneStructureGraphicsScene(QGraphicsScene):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        item = SceneBeatItem()
        self.addItem(item)

        item = self.addNewItem(item)
        self.addNewItem(item)

    def addNewItem(self, previous: SceneBeatItem) -> SceneBeatItem:
        item = SceneBeatItem()
        item.setPos(previous.scenePos() + QPointF(previous.boundingRect().width() - SceneBeatItem.OFFSET // 2, 0))
        self.addItem(item)

        return item


@spawn
class SceneStructureView(BaseGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel = Novel('My novel')

        self._wdgZoomBar = ZoomBar(self)
        self._wdgZoomBar.zoomed.connect(self._scale)

        self.setBackgroundBrush(QColor('#F2F2F2'))
        self._scene = SceneStructureGraphicsScene(self._novel)
        self.setScene(self._scene)

        # TODO remove later
        self.setMinimumSize(1600, 800)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._arrangeSideBars()

    @overrides
    def _scale(self, scale: float):
        super()._scale(scale)
        self._wdgZoomBar.updateScaledFactor(self.scaledFactor())

    def _arrangeSideBars(self):
        self._wdgZoomBar.setGeometry(10, self.height() - self._wdgZoomBar.sizeHint().height() - 10,
                                     self._wdgZoomBar.sizeHint().width(),
                                     self._wdgZoomBar.sizeHint().height())
