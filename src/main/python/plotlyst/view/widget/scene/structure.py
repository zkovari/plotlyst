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
import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QColor, QResizeEvent, QPainter, QPainterPath, QPen, QTransform, QPolygonF
from PyQt6.QtWidgets import QGraphicsScene, QAbstractGraphicsShapeItem, QWidget, QGraphicsItem, QGraphicsPolygonItem
from overrides import overrides

from plotlyst.common import PLOTLYST_TERTIARY_COLOR
from plotlyst.core.domain import Novel
from plotlyst.view.common import spawn
from plotlyst.view.widget.graphics import BaseGraphicsView
from plotlyst.view.widget.graphics.editor import ZoomBar
from plotlyst.view.widget.graphics.items import draw_bounding_rect, draw_point, draw_rect


@dataclass
class SceneBeat:
    text: str = ''
    angle: int = 0
    width: int = 180
    color: str = 'red'
    spacing: int = 17


class OutlineItemBase(QAbstractGraphicsShapeItem):
    OFFSET: int = 35

    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None):
        super().__init__(parent)
        self._beat = beat
        self._globalAngle = globalAngle
        self._width = 0
        self._height = 0
        self._timelineHeight = 86

        self._localCpPoint = QPointF(0, 0)
        self._calculateShape()

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        if self._globalAngle > 0:
            self.setRotation(-self._globalAngle)

    def item(self) -> SceneBeat:
        return self._beat

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
        draw_bounding_rect(painter, self, self._beat.color)
        draw_point(painter, self._localCpPoint, self._beat.color, 12)

    def connectionPoint(self) -> QPointF:
        return self.mapToScene(self._localCpPoint)

    @abstractmethod
    def adjustTo(self, previous: 'OutlineItemBase'):
        pass

    @abstractmethod
    def _calculateShape(self):
        pass

    @abstractmethod
    def _draw(self, painter: QPainter):
        pass


class StraightOutlineItem(OutlineItemBase):

    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None):
        self._path = QPainterPath()
        super().__init__(beat, globalAngle, parent)

    @overrides
    def shape(self) -> QPainterPath:
        return self._path

    @overrides
    def adjustTo(self, previous: 'OutlineItemBase'):
        diff = QPointF(self.OFFSET - previous.item().spacing, 0)

        if self._globalAngle > 0:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle < 0:
            diff.setX(self._width - diff.x())

        self.setPos(previous.connectionPoint() - diff)

    @overrides
    def _calculateShape(self):
        self._width = self._beat.width + self.OFFSET * 2
        self._height = self._timelineHeight

        if self._globalAngle >= 0:
            self._localCpPoint = QPointF(self._width, 0)
        else:
            self._localCpPoint = QPointF(0, 0)

        base_shape = [
            QPointF(0, 0),  # Top left point
            QPointF(self.OFFSET, self._timelineHeight / 2),  # Center left point
            QPointF(0, self._timelineHeight),  # Bottom left point
            QPointF(self._width - self.OFFSET, self._timelineHeight),  # Bottom right point
            QPointF(self._width, self._timelineHeight / 2),  # Center right point with offset
            QPointF(self._width - self.OFFSET, 0)  # Top right point
        ]

        if self._globalAngle == -180:
            shape = [QPointF(self._width - point.x(), point.y()) for point in base_shape]
        else:
            shape = base_shape

        for point in shape:
            self._path.lineTo(point)

    @overrides
    def _draw(self, painter: QPainter):
        painter.drawPath(self._path)

        painter.setPen(QPen(QColor('black'), 1))
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, self._beat.text)


class UTurnOutlineItem(OutlineItemBase):

    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None):
        self._arcRect = QRectF()
        self._topStartX = 0
        super().__init__(beat, globalAngle, parent)

    @overrides
    def adjustTo(self, previous: 'OutlineItemBase'):
        diff = QPointF(self._topStartX + self.OFFSET - previous.item().spacing, 0)

        if self._globalAngle > 0:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle < 0:
            diff.setX(self._width - diff.x())

        self.setPos(previous.connectionPoint() - diff)

    @overrides
    def _calculateShape(self):
        self._height = 350
        arcWidth = 200
        self._width = self._beat.width + arcWidth + self._timelineHeight

        if self._globalAngle >= 0:
            self._localCpPoint = QPointF(0, self._height - self._timelineHeight)
        else:
            self._localCpPoint = QPointF(self._width, self._height - self._timelineHeight)

        pen_half = self._timelineHeight // 2
        arc_margin = 8  # needed for slight adjustment

        if self._globalAngle >= 0:
            arc_x_start = self._beat.width + self.OFFSET + pen_half
            self._arcRect = QRectF(arc_x_start - pen_half, pen_half, arcWidth, self._height - self._timelineHeight)
        else:
            arc_x_start = pen_half + arc_margin
            self._arcRect = QRectF(arc_x_start, pen_half, arcWidth, self._height - self._timelineHeight)

        self._topStartX = self._width - self._arcRect.width() - self.OFFSET - self._timelineHeight - arc_margin

    @overrides
    def _draw(self, painter: QPainter):
        top_curve_shape = [
            QPointF(self._topStartX, 0),  # Top left point
            QPointF(self._topStartX + self.OFFSET, self._timelineHeight / 2),  # Center left point
            QPointF(self._topStartX, self._timelineHeight),  # Bottom left point
            QPointF(self._topStartX + self.OFFSET, self._timelineHeight),  # Bottom right point
            QPointF(self._topStartX + self.OFFSET, 0)  # Top right point
        ]

        y = self._height - self._timelineHeight
        bottom_curve_shape = [
            QPointF(self._beat.width + self.OFFSET + self._timelineHeight, y),  # Top right point
            QPointF(self._beat.width + self.OFFSET + self._timelineHeight, y + self._timelineHeight),  # Bottom right
            QPointF(self.OFFSET, y + self._timelineHeight),  # Bottom left point with offset
            QPointF(0, y + self._timelineHeight / 2),  # Center left point
            QPointF(self.OFFSET, y)  # Top left point with offset
        ]

        # Mirror the shape points if _globalAngle is negative
        if self._globalAngle < 0:
            top_curve_shape = [QPointF(self._width - point.x(), point.y())
                               for
                               point in
                               top_curve_shape]
            bottom_curve_shape = [QPointF(self._width - point.x(), point.y()) for
                                  point in bottom_curve_shape]

        painter.drawConvexPolygon(top_curve_shape)
        painter.drawConvexPolygon(bottom_curve_shape)

        pen = painter.pen()
        pen.setWidth(self._timelineHeight)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        if self._globalAngle >= 0:
            path.moveTo(self._arcRect.x(), self._arcRect.y())
            path.arcTo(self._arcRect, 90, -180)
        else:
            path.moveTo(self._arcRect.x() + self._arcRect.width(), self._arcRect.y())
            path.arcTo(self._arcRect, 90, 180)

        painter.drawPath(path)
        draw_rect(painter, self._arcRect)

        painter.setPen(QPen(QColor('black'), 1))
        painter.drawText(0, y, self._beat.width, self._timelineHeight, Qt.AlignmentFlag.AlignCenter, self._beat.text)


class _BaseShapeItem(QGraphicsPolygonItem):
    OFFSET: int = 35

    def __init__(self, beat: SceneBeat, parent=None):
        super().__init__(parent)
        self._beat = beat
        self._timelineHeight = 85

        top_shape_points = [
            QPointF(0, 0),  # Top left point
            QPointF(self.OFFSET, self._timelineHeight / 2),  # Center left point
            QPointF(0, self._timelineHeight),  # Bottom left point
            QPointF(self._beat.width - self.OFFSET, self._timelineHeight),  # Bottom right point
            QPointF(self._beat.width, self._timelineHeight / 2),  # Center right point with offset
            QPointF(self._beat.width - self.OFFSET, 0)  # Top right point
        ]
        polygon = QPolygonF(top_shape_points)
        self.setPolygon(polygon)
        self.setPen(QPen(QColor('grey'), 0))
        self.setBrush(QColor('grey'))

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    @overrides
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            print(f'shape pos {value}')
            self.parentItem().update()
        return super().itemChange(change, value)


class RisingOutlineItem(OutlineItemBase):
    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None):
        self._arcRect = QRectF()
        super().__init__(beat, globalAngle, parent)
        # self.setFlag(self.flags() | QGraphicsItem.GraphicsItemFlag.ItemClipsToShape)
        self._cp1Pos = QPointF(174, 286)
        # self._cp1 = BezierCPSocket(10, self)
        # self._cp1.setPos(self._cp1Pos)
        self._cp2Pos = QPointF(218, 178)
        # self._cp2 = BezierCPSocket(10, self)
        # self._cp2.setPos(self._cp2Pos)

        self._topShapePos = QPointF(236, 103)
        self._top_shape_item = _BaseShapeItem(self._beat, self)
        # self._top_shape_item = StraightOutlineItem(self._beat, 0, self)
        # self._top_shape_item.setRotation(-45)
        # self._top_shape_item.setPos(self._topShapePos)
        self._top_shape_item.setVisible(False)

    @overrides
    def adjustTo(self, previous: 'OutlineItemBase'):
        diff = QPointF(self.OFFSET - previous.item().spacing, self._height - self._timelineHeight)

        if self._globalAngle > 0:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle < 0:
            diff.setX(self._width - diff.x())

        self.setPos(previous.connectionPoint() - diff)

    def rearrangeCP(self, pos: QPointF):
        print(pos)
        self.update()

    @overrides
    def _calculateShape(self):
        self._width = 400
        arcSize = 150
        self._height = self._beat.width + arcSize

        if self._globalAngle >= 0:
            c = math.sqrt(self.OFFSET ** 2 + (self._timelineHeight // 2) ** 2)
            # self._localCpPoint = QPointF(self._width - c, 0)
            self._localCpPoint = QPointF(self._width, 0)

        pen_half = self._timelineHeight // 2
        arc_x_start = self.OFFSET + pen_half
        self._arcRect = QRectF(arc_x_start, pen_half, arcSize,
                               self._height - self._timelineHeight)

    @overrides
    def _draw(self, painter: QPainter):
        bottom_curve_shape = [
            QPointF(0, self._height - self._timelineHeight),  # Top left point
            QPointF(0 + self.OFFSET, self._height - self._timelineHeight / 2),  # Center left point
            QPointF(0, self._height),  # Bottom left point
            QPointF(0 + self.OFFSET, self._height),  # Bottom right point
            QPointF(0 + self.OFFSET, self._height - self._timelineHeight)  # Top right point
        ]
        painter.drawConvexPolygon(bottom_curve_shape)

        painter.save()
        painter.translate(self._topShapePos)
        painter.rotate(-45)
        painter.drawConvexPolygon(self._top_shape_item.polygon())
        painter.setPen(QPen(QColor('black'), 1))
        painter.drawText(0, 0, self._beat.width, self._timelineHeight, Qt.AlignmentFlag.AlignCenter, self._beat.text)
        painter.restore()

        pen = painter.pen()
        pen.setWidth(self._timelineHeight)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        pen_half = self._timelineHeight // 2

        path = QPainterPath()
        if self._globalAngle >= 0:
            path.moveTo(self._arcRect.x(), self._height - pen_half)
            x = self.OFFSET + pen_half
            y = self._height - pen_half - 5
            path.cubicTo(self._cp1Pos, self._cp2Pos,
                         self._topShapePos + QPointF(pen_half - 5, pen_half // 2))

        painter.drawPath(path)
        draw_rect(painter, self._arcRect)


class SceneStructureGraphicsScene(QGraphicsScene):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._globalAngle = 0

        item = StraightOutlineItem(SceneBeat(text='1', width=50, spacing=17), self._globalAngle)
        self.addItem(item)

        item = self.addNewItem(SceneBeat(text='2', width=135, color='blue'), item)
        item = self.addNewItem(SceneBeat(text='Rising', angle=45, color='green'), item)
        item = self.addNewItem(SceneBeat('3'), item)
        # item = self.addNewItem(SceneBeat(text='Curved 2', angle=-180), item)
        # item = self.addNewItem(SceneBeat('4'), item)
        # item = self.addNewItem(SceneBeat('4'), item)
        # item = self.addNewItem(SceneBeat('4'), item)
        # item = self.addNewItem(SceneBeat(text='Curved', angle=-180, color='green'), item)

    def addNewItem(self, beat: SceneBeat, previous: OutlineItemBase) -> OutlineItemBase:
        if beat.angle == 0:
            item = StraightOutlineItem(beat, self._globalAngle)
        elif beat.angle == 45:
            item = RisingOutlineItem(beat, self._globalAngle)
        else:
            item = UTurnOutlineItem(beat, self._globalAngle)

        item.adjustTo(previous)
        self.addItem(item)

        self._globalAngle += beat.angle
        if self._globalAngle == -360:
            self._globalAngle = 0

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
