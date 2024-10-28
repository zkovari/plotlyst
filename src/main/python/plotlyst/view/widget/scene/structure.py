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
from PyQt6.QtGui import QColor, QResizeEvent, QPainter, QPen, QPainterPath
from PyQt6.QtWidgets import QGraphicsScene, QAbstractGraphicsShapeItem, QWidget, QGraphicsItem
from overrides import overrides

from plotlyst.common import PLOTLYST_MAIN_COLOR, PLOTLYST_TERTIARY_COLOR
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

        self._timelineHeight = 85

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
            painter.setPen(QPen(QColor('grey'), 1))
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
                # QPointF(self._width - self.OFFSET, y + self._timelineHeight / 2),  # Center right point
                QPointF(self._width, y + self._timelineHeight),  # Bottom right point
                QPointF(self.OFFSET, y + self._timelineHeight),  # Bottom left point
                QPointF(0, y + self._timelineHeight / 2),  # Center left point with offset
                QPointF(self.OFFSET, y)  # Top left point
            ])

            painter.setPen(QPen(QColor('grey'), self._timelineHeight))
            painter.setBrush(Qt.BrushStyle.NoBrush)

            path = QPainterPath()
            pen_half = self._timelineHeight // 2
            path.moveTo(self.OFFSET + pen_half, pen_half)
            path.arcTo(QRectF(pen_half, pen_half, self._width - self.OFFSET - self._timelineHeight, self._height),
                       90, -180)
            # path.lineTo(self.OFFSET, y)
            # path.arcTo(
            #     QRectF(0, self._timelineHeight, self._timelineHeight,
            #            self._height - self._timelineHeight * 2),
            #     90, -180)
            # path.lineTo(0, 0)
            painter.drawPath(path)

            # self._drawCurve(painter)

        # painter.setFont(self._font)
        # painter.drawText(self._textRect, Qt.AlignmentFlag.AlignCenter,
        #                  self._text if self._text else self._placeholderText)

    def _drawCurve(self, painter: QPainter):
        # Initialize QPainterPath for the connected shape
        path = QPainterPath()

        # First trapezoid points (left trapezoid)
        top_left = QPointF(0, 0)
        center_left = QPointF(self.OFFSET, self._timelineHeight / 2)
        bottom_left = QPointF(0, self._timelineHeight)
        bottom_right = QPointF(self.OFFSET, self._timelineHeight)
        top_right = QPointF(self.OFFSET, 0)

        # Start the path with the first trapezoid
        path.moveTo(top_left)
        path.lineTo(center_left)
        path.lineTo(bottom_left)
        path.lineTo(bottom_right)
        path.lineTo(top_right)

        # Define the y position for the second trapezoid
        y = self._height - self._timelineHeight

        # Second trapezoid points (right trapezoid)
        top_right_2 = QPointF(self._width, y)  # Top right point
        center_right = QPointF(self._width - self.OFFSET, y + self._timelineHeight / 2)  # Center right point
        bottom_right_2 = QPointF(self._width, y + self._timelineHeight)  # Bottom right point
        bottom_left_2 = QPointF(self.OFFSET, y + self._timelineHeight)  # Bottom left point
        center_left_2 = QPointF(0, y + self._timelineHeight / 2)  # Center left point
        top_left_2 = QPointF(self.OFFSET, y)  # Top left point

        # Create a curve connecting the trapezoids
        # Connect top right of the first shape to the bottom right of the second shape
        path.lineTo(top_right)  # Finalize the first shape
        path.quadTo(
            QPointF(self._width / 2, self._timelineHeight),  # Control point for the curve
            bottom_right_2  # Bottom right of the second trapezoid
        )

        # Now connect the bottom right of the first to the top left of the second
        path.lineTo(bottom_left_2)  # Continue to the bottom left of the second trapezoid
        path.lineTo(bottom_right_2)  # Bottom right point
        path.lineTo(center_right)  # Continue to center right point
        path.lineTo(top_right_2)  # Top right point
        path.lineTo(center_left_2)  # Connect to center left of the second trapezoid
        path.lineTo(top_left_2)  # Finalize the second shape

        # Draw the entire connected shape with the curve
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
