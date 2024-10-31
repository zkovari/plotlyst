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
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional

from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QColor, QResizeEvent, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsScene, QAbstractGraphicsShapeItem, QWidget, QGraphicsItem
from overrides import overrides

from plotlyst.common import PLOTLYST_TERTIARY_COLOR
from plotlyst.core.domain import Novel
from plotlyst.view.common import spawn
from plotlyst.view.widget.graphics import BaseGraphicsView
from plotlyst.view.widget.graphics.editor import ZoomBar
from plotlyst.view.widget.graphics.items import draw_rect


@dataclass
class SceneBeat:
    angle: int = 0
    width: int = 180
    color: str = 'red'


class OutlineItemBase(QAbstractGraphicsShapeItem):
    OFFSET: int = 35

    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None):
        super().__init__(parent)
        self._beat = beat
        self._globalAngle = globalAngle
        self._width = 0
        self._height = 0
        self._timelineHeight = 86

        self._calculateSize()

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

        self._draw(painter)
        draw_rect(painter, self, self._beat.color)

    @abstractmethod
    def connectionPoint(self) -> QPointF:
        pass

    @abstractmethod
    def _calculateSize(self):
        pass

    @abstractmethod
    def _draw(self, painter: QPainter):
        pass


class StraightOutlineItem(OutlineItemBase):

    @overrides
    def connectionPoint(self) -> QPointF:
        return self.scenePos() + QPointF(self.boundingRect().width(), 0)

    @overrides
    def _calculateSize(self):
        self._width = self._beat.width + self.OFFSET * 2
        self._height = self._timelineHeight

    @overrides
    def _draw(self, painter: QPainter):
        base_shape = [
            QPointF(0, 0),  # Top left point
            QPointF(self.OFFSET, self._timelineHeight / 2),  # Center left point
            QPointF(0, self._timelineHeight),  # Bottom left point
            QPointF(self._width - self.OFFSET, self._timelineHeight),  # Bottom right point
            QPointF(self._width, self._timelineHeight / 2),  # Center right point with offset
            QPointF(self._width - self.OFFSET, 0)  # Top right point
        ]

        shape = base_shape if self._globalAngle == 0 else [
            QPointF(self._width - point.x(), point.y()) for point in base_shape
        ]

        painter.drawConvexPolygon(shape)


class UTurnOutlineItem(OutlineItemBase):

    @overrides
    def connectionPoint(self) -> QPointF:
        return self.pos() + QPointF(0, self._height - self._timelineHeight)

    @overrides
    def _calculateSize(self):
        self._width = self._beat.width * 2 + self.OFFSET * 2
        self._xDiff = 75
        self._width += self._xDiff
        self._height = 350

    @overrides
    def _draw(self, painter: QPainter):
        x = self._beat.width
        y = self._height - self._timelineHeight

        # Define the base shape points for the two convex polygons
        top_curve_shape = [
            QPointF(x, 0),  # Top left point
            QPointF(x + self.OFFSET, self._timelineHeight / 2),  # Center left point
            QPointF(x, self._timelineHeight),  # Bottom left point
            QPointF(x + self.OFFSET, self._timelineHeight),  # Bottom right point
            QPointF(x + self.OFFSET, 0)  # Top right point
        ]

        bottom_curve_shape = [
            QPointF(self._beat.width + self.OFFSET + self._timelineHeight, y),  # Top right point
            QPointF(self._beat.width + self.OFFSET + self._timelineHeight, y + self._timelineHeight),
            # Bottom right point
            QPointF(self.OFFSET, y + self._timelineHeight),  # Bottom left point with offset
            QPointF(0, y + self._timelineHeight / 2),  # Center left point
            QPointF(self.OFFSET, y)  # Top left point with offset
        ]

        # Mirror the shape points if _globalAngle is negative
        if self._globalAngle < 0:
            top_curve_shape = [QPointF(self._width - point.x() + self._timelineHeight * 2, point.y())
                               for
                               point in
                               top_curve_shape]
            bottom_curve_shape = [QPointF(self._width - point.x() + self._timelineHeight * 2, point.y()) for
                                  point in bottom_curve_shape]

        painter.drawConvexPolygon(top_curve_shape)
        painter.drawConvexPolygon(bottom_curve_shape)

        pen = painter.pen()
        pen.setWidth(self._timelineHeight)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        pen_half = self._timelineHeight // 2

        arc_x_start = x + self.OFFSET + pen_half
        if self._globalAngle < 0:
            arc_x_start = self._width - arc_x_start

        path.moveTo(arc_x_start, pen_half)
        path.arcTo(QRectF(
            arc_x_start - pen_half, pen_half,
            self._width - self.OFFSET - self._timelineHeight,
            self._height - self._timelineHeight
        ), 90, -180)

        painter.drawPath(path)


class SceneStructureGraphicsScene(QGraphicsScene):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._globalAngle = 0
        self._spacing = 17

        item = StraightOutlineItem(SceneBeat(width=350), self._globalAngle)
        self.addItem(item)

        item = self.addNewItem(SceneBeat(width=135, color='blue'), item)
        # item = self.addNewItem(SceneBeat(angle=-180, color='green'), item)
        item = self.addNewItem(SceneBeat(), item)
        # item = self.addNewItem(SceneBeat(angle=-180), item)

    def addNewItem(self, beat: SceneBeat, previous: OutlineItemBase) -> OutlineItemBase:
        if beat.angle == 0:
            item = StraightOutlineItem(beat, self._globalAngle)
        else:
            item = UTurnOutlineItem(beat, self._globalAngle)

        overlap = self._spacing
        if beat.angle < 0:
            overlap += beat.width

        if self._globalAngle == 0:
            item.setPos(previous.connectionPoint() - QPointF(overlap, 0))
        elif self._globalAngle < 0:
            if beat.angle == 0:
                item.setPos(previous.connectionPoint() - QPointF(item.boundingRect().width() - overlap, 0))
            else:
                print(overlap)
                print(item.boundingRect().width())
                item.setPos(previous.connectionPoint() - QPointF(item.boundingRect().width() - overlap, 0))

        self._globalAngle += beat.angle

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
