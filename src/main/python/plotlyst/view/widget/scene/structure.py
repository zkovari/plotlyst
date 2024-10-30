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


class TimelineElementShape(Enum):
    Straight = 0
    Curve_left = 1
    Curve_right = 1


class TimelineElementDirection(Enum):
    Left = 0
    Right = 1
    Top = 2
    Bottom = 3

    def opposite(self) -> 'TimelineElementDirection':
        if self == TimelineElementDirection.Left:
            return TimelineElementDirection.Right
        if self == TimelineElementDirection.Right:
            return TimelineElementDirection.Left
        if self == TimelineElementDirection.Top:
            return TimelineElementDirection.Bottom
        if self == TimelineElementDirection.Bottom:
            return TimelineElementDirection.Top


@dataclass
class SceneBeat:
    shape: TimelineElementShape = TimelineElementShape.Straight
    width: int = 180


class SceneBeatItem(QAbstractGraphicsShapeItem):
    OFFSET: int = 35

    def __init__(self, beat: SceneBeat, direction: TimelineElementDirection, parent=None):
        super().__init__(parent)
        self._beat = beat
        self._direction = direction
        print(self._direction)
        self._width = self._beat.width + self.OFFSET * 2
        self._xDiff = 0
        if self._beat.shape == TimelineElementShape.Straight:
            self._height = 86
        else:
            self._xDiff = 75
            self._width += self._xDiff
            self._height = 350

        self._timelineHeight = 86

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def direction(self) -> TimelineElementDirection:
        return self._direction

    def connectionPoint(self) -> QPointF:
        if self._beat.shape == TimelineElementShape.Straight:
            return self.scenePos() + QPointF(self.boundingRect().width(), 0)
        elif self._beat.shape == TimelineElementShape.Curve_right:
            return self.scenePos() + QPointF(0, self._height - self._timelineHeight)
        else:
            return self.scenePos() + QPointF(self.boundingRect().width(), 0)

    @overrides
    def boundingRect(self) -> QRectF:
        diff = 0 if self._beat.shape == TimelineElementShape.Straight else self._beat.width
        return QRectF(0, 0, self._width + diff, self._height)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(QColor(PLOTLYST_TERTIARY_COLOR), 0))
            painter.setBrush(QColor(PLOTLYST_TERTIARY_COLOR))
        else:
            painter.setPen(QPen(QColor('grey'), 0))
            painter.setBrush(QColor('grey'))

        if self._beat.shape == TimelineElementShape.Straight:
            if self._direction == TimelineElementDirection.Right:
                painter.drawConvexPolygon([
                    QPointF(0, 0),  # Top left point
                    QPointF(self.OFFSET, self._timelineHeight / 2),  # Center left point
                    QPointF(0, self._timelineHeight),  # Bottom left point
                    QPointF(self._width - self.OFFSET, self._timelineHeight),  # Bottom right point
                    QPointF(self._width, self._timelineHeight / 2),  # Center right point with offset
                    QPointF(self._width - self.OFFSET, 0)  # Top right point
                ])
            else:
                painter.drawConvexPolygon([
                    QPointF(self._width, 0),  # Top right point
                    QPointF(self._width - self.OFFSET, self._timelineHeight / 2),  # Center right point with offset
                    QPointF(self._width, self._timelineHeight),  # Bottom right point
                    QPointF(self.OFFSET, self._timelineHeight),  # Bottom left point
                    QPointF(0, self._timelineHeight / 2),  # Center left point
                    QPointF(self.OFFSET, 0)  # Top left point
                ])
        elif self._beat.shape == TimelineElementShape.Curve_right:
            x = self._beat.width
            painter.drawConvexPolygon([
                QPointF(x, 0),  # Top left point
                QPointF(x + self.OFFSET, self._timelineHeight / 2),  # Center left point
                QPointF(x, self._timelineHeight),  # Bottom left point
                QPointF(x + self.OFFSET, self._timelineHeight),  # Bottom right point
                QPointF(x + self.OFFSET, 0)  # Top right point
            ])

            y = self._height - self._timelineHeight
            painter.drawConvexPolygon([
                QPointF(self._beat.width + self.OFFSET + self._timelineHeight, y),  # Top right point
                QPointF(self._beat.width + self.OFFSET + self._timelineHeight, y + self._timelineHeight),
                # Bottom right point
                QPointF(self.OFFSET, y + self._timelineHeight),  # Bottom left point with offset
                QPointF(0, y + self._timelineHeight / 2),  # Center left point
                QPointF(self.OFFSET, y)  # Top left point with offset
            ])

            pen = painter.pen()
            pen.setWidth(self._timelineHeight)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            path = QPainterPath()
            pen_half = self._timelineHeight // 2
            path.moveTo(x + self.OFFSET + pen_half, pen_half)
            path.arcTo(QRectF(x + pen_half, pen_half,
                              self._width - self.OFFSET - self._timelineHeight,
                              self._height - self._timelineHeight),
                       90, -180)

            painter.drawPath(path)


class SceneStructureGraphicsScene(QGraphicsScene):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        item = SceneBeatItem(SceneBeat(width=350), TimelineElementDirection.Right)
        self.addItem(item)

        item = self.addNewItem(SceneBeat(width=135), item)
        item = self.addNewItem(SceneBeat(TimelineElementShape.Curve_right), item)
        self.addNewItem(SceneBeat(), item)

    def addNewItem(self, beat: SceneBeat, previous: SceneBeatItem) -> SceneBeatItem:
        if beat.shape == TimelineElementShape.Straight:
            direction = previous.direction()
        else:
            direction = previous.direction().opposite()
        item = SceneBeatItem(beat, direction)
        overlap = SceneBeatItem.OFFSET // 2
        if beat.shape != TimelineElementShape.Straight:
            overlap += beat.width

        if previous.direction() == TimelineElementDirection.Right:
            item.setPos(previous.connectionPoint() - QPointF(overlap, 0))
        elif previous.direction() == TimelineElementDirection.Left:
            item.setPos(previous.connectionPoint() - QPointF(item.boundingRect().width() - overlap, 0))

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
