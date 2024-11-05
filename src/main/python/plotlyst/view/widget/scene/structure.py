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
from typing import Optional, Any, List

from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QTransform, QPolygonF
from PyQt6.QtWidgets import QAbstractGraphicsShapeItem, QWidget, QGraphicsItem, QGraphicsPolygonItem, \
    QApplication, QGraphicsSceneMouseEvent
from overrides import overrides
from qthandy import pointy

from plotlyst.common import PLOTLYST_TERTIARY_COLOR, RELAXED_WHITE_COLOR
from plotlyst.core.domain import Novel, Node, GraphicsItemType
from plotlyst.view.common import shadow, stronger_color, blended_color_with_alpha
from plotlyst.view.style.theme import BG_MUTED_COLOR
from plotlyst.view.widget.graphics import NetworkGraphicsView, NetworkScene
from plotlyst.view.widget.graphics.editor import ConnectorToolbar
from plotlyst.view.widget.graphics.items import IconItem


@dataclass
class SceneBeat:
    text: str = ''
    angle: int = 0
    width: int = 180
    icon: str = ''
    color: str = ''
    spacing: int = 17
    icon_size: int = 60
    icon_frame: bool = False


class OutlineItemBase(QAbstractGraphicsShapeItem):
    OFFSET: int = 35

    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None, placeholder: bool = False):
        super().__init__(parent)
        self._beat = beat
        self._globalAngle = globalAngle
        self._placeholder = placeholder
        self._width = 0
        self._height = 0
        self._timelineHeight = 86

        self._bgColor = QColor(RELAXED_WHITE_COLOR)
        self._hoveredBgColor = QColor(stronger_color(RELAXED_WHITE_COLOR, factor=0.99))
        if self._beat.color:
            self._selectedColor = QColor(blended_color_with_alpha(self._beat.color, alpha=155))
            self._hoveredSelectedColor = QColor(blended_color_with_alpha(self._beat.color, alpha=175))
        else:
            self._selectedColor = QColor(PLOTLYST_TERTIARY_COLOR)
            self._hoveredSelectedColor = QColor(stronger_color(PLOTLYST_TERTIARY_COLOR, factor=0.99))
        self._hovered: bool = False

        self._font = QApplication.font()
        self._font.setPointSize(18)

        self._localCpPoint = QPointF(0, 0)
        self._iconSize = self._beat.icon_size
        self._iconRectSize = self._iconSize + 2 * IconItem.Margin
        # self._iconRectSize = self._iconSize
        self._iconItem = IconItem(
            Node(self.OFFSET // 2, -(self._iconRectSize - self._timelineHeight) // 2, GraphicsItemType.ICON,
                 size=self._iconSize,
                 icon=self._beat.icon, color=self._beat.color), self)
        if self._beat.icon_frame:
            self._iconItem.setFrameEnabled(True)

        self._calculateShape()

        if self._placeholder:
            pointy(self)
            self.setOpacity(0.05)
        else:
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        if not self._beat.icon:
            self._iconItem.setVisible(False)

        if self._globalAngle >= -45:
            self.setRotation(-self._globalAngle)
        elif self._globalAngle == -135:
            self.setRotation(-45)

        self._shadow()

    def item(self) -> SceneBeat:
        return self._beat

    def structureScene(self) -> 'SceneStructureGraphicsScene':
        return self.scene()

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self._placeholder:
            color = 'grey' if self._hovered else 'lightgrey'
            qcolor = QColor(blended_color_with_alpha(color, alpha=115))
        elif self.isSelected():
            qcolor = self._hoveredSelectedColor if self._hovered else self._selectedColor
        else:
            qcolor = self._hoveredBgColor if self._hovered else self._bgColor
        painter.setPen(QPen(qcolor, 0))
        painter.setBrush(qcolor)

        self._draw(painter)
        # draw_bounding_rect(painter, self, self._beat.color)
        # draw_point(painter, self._localCpPoint, self._beat.color, 12)

    # @overrides
    # def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
    #     if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
    #         self._onSelection(value)
    #     return super().itemChange(change, value)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = True
        self.update()
        self._shadow(10)
        if self._placeholder:
            self.setOpacity(1.0)

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = False
        self.update()
        self._shadow()
        if self._placeholder:
            self.setOpacity(0.05)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        super().mouseReleaseEvent(event)
        self.structureScene().placeholderClickedEvent(self)

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

    def _shadow(self, radius: int = 25):
        if not self._placeholder:
            shadow(self, offset=0, radius=radius, color=self._beat.color)


class StraightOutlineItem(OutlineItemBase):

    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None, placeholder: bool = False):
        self._path = QPainterPath()
        super().__init__(beat, globalAngle, parent, placeholder)

    @overrides
    def shape(self) -> QPainterPath:
        return self._path

    @overrides
    def adjustTo(self, previous: 'OutlineItemBase'):
        diff = QPointF(self.OFFSET - previous.item().spacing, 0)

        if self._globalAngle > 0:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle == -45:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle == -135:
            diff.setX(self._width - diff.x())
            diff.setY(self._timelineHeight)
            transform = QTransform().rotate(-45)
            diff = transform.map(diff)
        elif self._globalAngle < 0:
            diff.setX(self._width - diff.x())

        self.setPos(previous.connectionPoint() - diff)

    @overrides
    def _calculateShape(self):
        self._width = self._beat.width + self.OFFSET * 2 + self._iconRectSize
        self._height = self._timelineHeight

        if self._globalAngle >= 0:
            self._localCpPoint = QPointF(self._width, 0)
        elif self._globalAngle == -45:
            self._localCpPoint = QPointF(self._width, 0)
        elif self._globalAngle == -135:
            self._localCpPoint = QPointF(0, self._height)
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

        if self._globalAngle == -180 or self._globalAngle == -135:
            shape = [QPointF(self._width - point.x(), point.y()) for point in base_shape]
        else:
            shape = base_shape

        for point in shape:
            self._path.lineTo(point)

    @overrides
    def _draw(self, painter: QPainter):
        painter.drawPath(self._path)

        painter.setFont(self._font)
        painter.setPen(QPen(QColor('black'), 1))
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, self._beat.text)


class UTurnOutlineItem(OutlineItemBase):

    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None, placeholder: bool = False):
        self._arcRect = QRectF()
        self._topStartX = 0
        super().__init__(beat, globalAngle, parent, placeholder)

    @overrides
    def adjustTo(self, previous: 'OutlineItemBase'):
        diff = QPointF(self._topStartX + self.OFFSET - previous.item().spacing, 0)

        if self._globalAngle > 0:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle == -135:
            diff.setX(self._width - diff.x())
            diff.setY(self._timelineHeight)
            transform = QTransform().rotate(-45)
            diff = transform.map(diff)
        elif self._globalAngle < 0:
            diff.setX(self._width - diff.x())

        self.setPos(previous.connectionPoint() - diff)

    @overrides
    def _calculateShape(self):
        self._height = 350
        arcWidth = 200
        self._width = self._beat.width + arcWidth + self._timelineHeight

        if self._globalAngle == 0:
            self._localCpPoint = QPointF(0, self._height - self._timelineHeight)
        elif self._globalAngle == 45:
            self._localCpPoint = QPointF(0, self._height)
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

        self._iconItem.setPos(
            self._width - self._timelineHeight - arc_margin - (self._iconRectSize - self._timelineHeight) // 2,
            (self._height - self._iconRectSize) // 2)

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
        # draw_rect(painter, self._arcRect)

        painter.setFont(self._font)
        painter.setPen(QPen(QColor('black'), 1))
        if self._globalAngle >= 0:
            painter.drawText(self.OFFSET, y, self._beat.width, self._timelineHeight, Qt.AlignmentFlag.AlignCenter,
                             self._beat.text)
        else:
            painter.drawText(int(self._arcRect.x() + self._arcRect.width() - self.OFFSET), y, self._beat.width,
                             self._timelineHeight,
                             Qt.AlignmentFlag.AlignCenter, self._beat.text)


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

    def topRightPoint(self) -> QPointF:
        return QPointF(self._beat.width - self.OFFSET, 0)

    def bottomRightPoint(self) -> QPointF:
        return QPointF(self._beat.width - self.OFFSET, self._timelineHeight)

    @overrides
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            print(f'shape pos {value}')
            if self.parentItem():
                self.parentItem().update()
        return super().itemChange(change, value)


class RisingOutlineItem(OutlineItemBase):
    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None, placeholder: bool = False):
        # y calculated later for these points
        self._cp1Pos = QPointF(169, 0)
        self._cp2Pos = QPointF(218, 0)
        self._quadStartPoint = QPointF(0, 0)
        self._topShapePos = QPointF(236, 0)
        self._topShapeItem = _BaseShapeItem(beat)
        super().__init__(beat, globalAngle, parent, placeholder)
        # self.setFlag(self.flags() | QGraphicsItem.GraphicsItemFlag.ItemClipsToShape)
        # self._cp1 = BezierCPSocket(10, self, index=1)
        # self._cp1.setPos(self._cp1Pos)
        # self._cp2 = BezierCPSocket(10, self, index=2)
        # self._cp2.setPos(self._cp2Pos)

        # self._top_shape_item = StraightOutlineItem(self._beat, 0, self)
        # self._topShapeItem.setParentItem(self)
        # self._topShapeItem.setRotation(-self._beat.angle)
        # self._topShapeItem.setPos(self._topShapePos)
        self._topShapeItem.setVisible(False)

    @overrides
    def adjustTo(self, previous: 'OutlineItemBase'):
        diff = QPointF(self.OFFSET - previous.item().spacing, self._height - self._timelineHeight)

        if self._globalAngle > 0:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle == -45:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle < 0:
            diff.setX(self._width - diff.x())

        self.setPos(previous.connectionPoint() - diff)

    def rearrangeCP1(self, pos: QPointF):
        print(f'cp1 {pos}')
        self._cp1Pos.setX(pos.x())
        self._cp1Pos.setY(pos.y())
        self.update()

    def rearrangeCP2(self, pos: QPointF):
        print(f'cp2 {pos}')
        self._cp2Pos.setX(pos.x())
        self._cp2Pos.setY(pos.y())
        self.update()

    @overrides
    def _calculateShape(self):
        self._width = self._topShapePos.x()
        self._height = 227
        self._recalculateControlPoints()

        transform = QTransform()
        transform.translate(self._topShapePos.x(), self._topShapePos.y())
        transform.rotate(-self._beat.angle)

        transformed_point = transform.map(self._topShapeItem.bottomRightPoint())
        self._width = transformed_point.x()
        transformed_point = transform.map(self._topShapeItem.topRightPoint())
        self._height += abs(transformed_point.y())
        self._recalculateControlPoints()

        self._calculateConnectionPoint()

        self._iconItem.setPos(self.OFFSET,
                              self._height - self._timelineHeight - (self._iconRectSize - self._timelineHeight) // 2)

    def _recalculateControlPoints(self):
        # these numbers were found by manually moving BezierCPSocket points
        self._cp1Pos.setY(self._height - 44)
        self._cp2Pos.setY(self._height - 152)
        self._topShapePos.setY(self._height - 227)
        self._quadStartPoint.setX(self.OFFSET + self._timelineHeight // 2)
        self._quadStartPoint.setY(self._height - self._timelineHeight // 2)

    def _calculateConnectionPoint(self):
        if self._globalAngle >= 0:
            self._localCpPoint = QPointF(self._width - self._timelineHeight // 2 + 5, -24)
        else:
            self._localCpPoint = QPointF(self._width - 34, -self._timelineHeight // 2 + 15)

    @overrides
    def _draw(self, painter: QPainter):
        self._drawBeginning(painter)
        self._drawEnding(painter)

        pen = painter.pen()
        pen.setWidth(self._timelineHeight)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        self._drawCurve(painter)

        # draw_point(painter, self._topShapePos, 'red', 10)

    def _drawCurve(self, painter):
        pen_half = self._timelineHeight // 2
        path = QPainterPath()
        path.moveTo(self._quadStartPoint)
        path.cubicTo(self._cp1Pos, self._cp2Pos, self._topShapePos + QPointF(pen_half - 5, pen_half // 2))
        painter.drawPath(path)

    def _drawEnding(self, painter: QPainter):
        painter.save()

        painter.translate(self._topShapePos)
        painter.rotate(-self._beat.angle)
        painter.drawConvexPolygon(self._topShapeItem.polygon())

        painter.setFont(self._font)
        painter.setPen(QPen(QColor('black'), 1))
        painter.drawText(0, 0, self._beat.width, self._timelineHeight, Qt.AlignmentFlag.AlignCenter, self._beat.text)
        painter.restore()

    def _drawBeginning(self, painter: QPainter):
        bottom_curve_shape = [
            QPointF(0, self._height - self._timelineHeight),  # Top left point
            QPointF(0 + self.OFFSET, self._height - self._timelineHeight / 2),  # Center left point
            QPointF(0, self._height),  # Bottom left point
            QPointF(0 + self.OFFSET, self._height),  # Bottom right point
            QPointF(0 + self.OFFSET, self._height - self._timelineHeight)  # Top right point
        ]
        painter.drawConvexPolygon(bottom_curve_shape)


class FallingOutlineItem(RisingOutlineItem):

    def __init__(self, beat: SceneBeat, globalAngle: int, parent=None, placeholder: bool = False):
        super().__init__(beat, globalAngle, parent, placeholder)
        self._topShapeItem.setParentItem(self)
        self._topShapeItem.setRotation(-self._beat.angle)

    @overrides
    def adjustTo(self, previous: 'OutlineItemBase'):
        diff = QPointF(self.OFFSET - previous.item().spacing, 0)

        if self._globalAngle > 0:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle == -45:
            transform = QTransform().rotate(-self._globalAngle)
            diff = transform.map(diff)
        elif self._globalAngle < 0:
            diff.setX(self._width - diff.x())

        self.setPos(previous.connectionPoint() - diff)

    @overrides
    def _calculateShape(self):
        self._width = self._topShapePos.x()
        self._height = 227
        self._recalculateControlPoints()

        self._topShapeItem.setPos(QPointF(294, 164))
        transform = QTransform()
        transform.translate(self._topShapeItem.pos().x(), self._topShapeItem.pos().y())
        transform.rotate(-self._beat.angle)

        self._width = transform.map(self._topShapeItem.topRightPoint()).x()
        self._height = abs(transform.map(self._topShapeItem.bottomRightPoint()).y())
        self._recalculateControlPoints()

        self._calculateConnectionPoint()

    @overrides
    def _recalculateControlPoints(self):
        self._cp1Pos.setY(43)
        self._cp2Pos.setY(152)
        self._topShapePos.setY(227)
        self._quadStartPoint.setX(self.OFFSET + self._timelineHeight // 2)
        self._quadStartPoint.setY(self._timelineHeight // 2)

    @overrides
    def _calculateConnectionPoint(self):
        if self._globalAngle >= 0:
            # self._localCpPoint = QPointF(self._width - self._timelineHeight // 2 + 5, -24)

            # self._localCpPoint = QPointF(self._width + self._timelineHeight // 2 - 5, self._height - 24)
            self._localCpPoint = QPointF(self._width + 24, self._height - self._timelineHeight // 2 + 5)

    @overrides
    def _drawBeginning(self, painter):
        bottom_curve_shape = [
            QPointF(0, 0),  # Top left point
            QPointF(0 + self.OFFSET, self._timelineHeight / 2),  # Center left point
            QPointF(0, self._timelineHeight),  # Bottom left point
            QPointF(0 + self.OFFSET, self._timelineHeight),  # Bottom right point
            QPointF(0 + self.OFFSET, 0)  # Top right point
        ]
        painter.drawConvexPolygon(bottom_curve_shape)

    @overrides
    def _drawEnding(self, painter: QPainter):
        painter.save()
        painter.translate(self._topShapeItem.pos())
        painter.rotate(-self._beat.angle)
        painter.drawConvexPolygon(self._topShapeItem.polygon())

        painter.setFont(self._font)
        painter.setPen(QPen(QColor('black'), 1))
        painter.drawText(0, 0, self._beat.width, self._timelineHeight, Qt.AlignmentFlag.AlignCenter, self._beat.text)
        painter.restore()

    @overrides
    def _drawCurve(self, painter):
        pen_half = self._timelineHeight // 2
        path = QPainterPath()
        path.moveTo(self._quadStartPoint)
        path.cubicTo(self._cp1Pos, self._cp2Pos, self._topShapePos + QPointF(pen_half - 5, -pen_half // 2))
        painter.drawPath(path)


class SceneStructureGraphicsScene(NetworkScene):
    DEFAULT_ANGLE = 0

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._globalAngle = self.DEFAULT_ANGLE

        item = StraightOutlineItem(SceneBeat(text='Goal', width=120, spacing=17, icon='mdi.target', color='darkBlue'),
                                   self._globalAngle)
        item.setPos(0, -100)
        self.addItem(item)

        item = self.addNewItem(SceneBeat(text='2', width=135), item)
        item = self.addNewItem(SceneBeat(text='Setback', angle=-45, color='#FD4D21', icon='mdi.chemical-weapon'), item)
        # item = self.addNewItem(SceneBeat('3/a'), item)
        item = self.addNewItem(SceneBeat('Progress', angle=45, icon='mdi6.progress-upload'), item)
        item = self.addNewItem(SceneBeat(text='U-turn', angle=-180), item)
        # item = self.addNewItem(SceneBeat(text='Falling', angle=-45, color='green'), item)

        self._lastItem = item
        self._placeholders: List[OutlineItemBase] = []

        self._drawBottom()

    def _drawBottom(self):
        self._globalAngle = self.DEFAULT_ANGLE
        item = StraightOutlineItem(SceneBeat(text='Other item', width=50, spacing=17), self._globalAngle)
        item.setPos(0, 100)
        self.addItem(item)
        item = self.addNewItem(SceneBeat(text='Conflict', width=135, icon='mdi.sword-cross', color='#f3a712'), item)
        item = self.addNewItem(SceneBeat(text='Rising', angle=45, color='#08605f', icon='mdi6.progress-upload'), item)
        item = self.addNewItem(SceneBeat('3'), item)
        item = self.addNewItem(
            SceneBeat(text='Inciting', width=100, icon='mdi.bell-alert-outline', color='#a2ad59'), item)
        item = self.addNewItem(SceneBeat('6', width=30), item)
        item = self.addNewItem(
            SceneBeat(text='Crisis', width=100, angle=-180, icon='mdi.arrow-decision-outline', color='#ce2d4f',
                      icon_size=150, icon_frame=True), item)
        item = self.addNewItem(SceneBeat('7', width=30, icon='fa5s.map-signs', color='#ba6f4d'), item)
        item = self.addNewItem(SceneBeat(text='Rising 3', width=100, angle=-180, color='#08605f'), item)

        self._lastItem = item

        self._addPlaceholders(item)

    def addNewItem(self, beat: SceneBeat, previous: OutlineItemBase) -> OutlineItemBase:
        item = self._initOutlineItem(beat)
        item.adjustTo(previous)
        self.addItem(item)

        self._globalAngle += beat.angle
        if self._globalAngle == -360:
            self._globalAngle = 0
        elif self._globalAngle == -315:
            self._globalAngle = 45

        return item

    def placeholderClickedEvent(self, placeholder: OutlineItemBase):
        newItem = self.addNewItem(SceneBeat('Beat', angle=placeholder.item().angle), self._lastItem)
        self._lastItem = newItem

        for placeholderItem in self._placeholders:
            placeholderItem.adjustTo(newItem)

    def _addPlaceholders(self, last: OutlineItemBase):
        placeholders = [
            SceneBeat('Add new turning item', angle=-180),
            SceneBeat('Add new rising item', angle=45),
            SceneBeat('Add new falling item', angle=-45),
            SceneBeat('Add new straight item'),
        ]

        for placeholder in placeholders:
            item = self._initOutlineItem(placeholder, placeholder=True)
            self._placeholders.append(item)
            item.adjustTo(last)
            self.addItem(item)

    def _initOutlineItem(self, beat: SceneBeat, placeholder: bool = False):
        if beat.angle == 0:
            item = StraightOutlineItem(beat, self._globalAngle, placeholder=placeholder)
        elif beat.angle == 45:
            item = RisingOutlineItem(beat, self._globalAngle, placeholder=placeholder)
        elif beat.angle == -45:
            item = FallingOutlineItem(beat, self._globalAngle, placeholder=placeholder)
        else:
            item = UTurnOutlineItem(beat, self._globalAngle, placeholder=placeholder)
        return item


class SceneStructureView(NetworkGraphicsView):
    def __init__(self, parent=None):
        self._novel = Novel('My novel')
        super().__init__(parent)
        self.setBackgroundBrush(QColor(BG_MUTED_COLOR))

        self._connectorEditor = ConnectorToolbar(self.undoStack, self)
        self._connectorEditor.setVisible(False)

        # TODO remove later
        self.setMinimumSize(1600, 800)

    @overrides
    def _initScene(self) -> NetworkScene:
        return SceneStructureGraphicsScene(self._novel)
