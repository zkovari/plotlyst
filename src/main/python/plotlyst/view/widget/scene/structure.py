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
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QColor, QResizeEvent, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsScene, QAbstractGraphicsShapeItem, QWidget, QGraphicsItem
from overrides import overrides

from plotlyst.common import PLOTLYST_TERTIARY_COLOR
from plotlyst.core.domain import Novel
from plotlyst.view.widget.graphics import BaseGraphicsView
from plotlyst.view.widget.graphics.editor import ZoomBar


class TimelineElementDirection(Enum):
    Straight = 0
    Curve_left = 1
    Curve_right = 1


@dataclass
class SceneBeat:
    direction: TimelineElementDirection = TimelineElementDirection.Straight


class SceneBeatItem(QAbstractGraphicsShapeItem):
    OFFSET: int = 35

    def __init__(self, beat: SceneBeat, parent=None):
        super().__init__(parent)
        self._beat = beat
        self._width = 250
        if self._beat.direction == TimelineElementDirection.Straight:
            self._height = 85
        else:
            self._height = 350

        self._timelineHeight = 86

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(QColor(PLOTLYST_TERTIARY_COLOR), 0))
            painter.setBrush(QColor(PLOTLYST_TERTIARY_COLOR))
        else:
            painter.setPen(QPen(QColor('grey'), 0))
            painter.setBrush(QColor('grey'))

        if self._beat.direction == TimelineElementDirection.Straight:
            painter.drawConvexPolygon([
                QPointF(0, 0),  # Top left point
                QPointF(self.OFFSET, self._timelineHeight / 2),  # Center left point
                QPointF(0, self._timelineHeight),  # Bottom left point
                QPointF(self._width - self.OFFSET, self._timelineHeight),  # Bottom right point
                QPointF(self._width, self._timelineHeight / 2),  # Center right point with offset
                QPointF(self._width - self.OFFSET, 0)  # Top right point
            ])
        elif self._beat.direction == TimelineElementDirection.Curve_right:
            painter.drawConvexPolygon([
                QPointF(0, 0),  # Top left point
                QPointF(self.OFFSET, self._timelineHeight / 2),  # Center left point
                QPointF(0, self._timelineHeight),  # Bottom left point
                QPointF(self.OFFSET, self._timelineHeight),  # Bottom right point
                QPointF(self.OFFSET, 0)  # Top right point
            ])

            y = self._height - self._timelineHeight
            painter.drawConvexPolygon([
                QPointF(self._width, y),  # Top right point
                QPointF(self._width, y + self._timelineHeight),  # Bottom right point
                QPointF(self.OFFSET, y + self._timelineHeight),  # Bottom left point
                QPointF(0, y + self._timelineHeight / 2),  # Center left point with offset
                QPointF(self.OFFSET, y)  # Top left point
            ])

            pen = painter.pen()
            pen.setWidth(self._timelineHeight)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            path = QPainterPath()
            pen_half = self._timelineHeight // 2
            path.moveTo(self.OFFSET + pen_half, pen_half)
            path.arcTo(QRectF(pen_half, pen_half, self._width - self.OFFSET - self._timelineHeight - pen_half,
                              self._height - self._timelineHeight),
                       90, -180)
            painter.drawPath(path)


class SceneStructureGraphicsScene(QGraphicsScene):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        item = SceneBeatItem(SceneBeat())
        self.addItem(item)

        item = self.addNewItem(SceneBeat(), item)
        self.addNewItem(SceneBeat(TimelineElementDirection.Curve_right), item)

    def addNewItem(self, beat: SceneBeat, previous: SceneBeatItem) -> SceneBeatItem:
        item = SceneBeatItem(beat)
        item.setPos(previous.scenePos() + QPointF(previous.boundingRect().width() - SceneBeatItem.OFFSET // 2, 0))
        self.addItem(item)

        return item


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
