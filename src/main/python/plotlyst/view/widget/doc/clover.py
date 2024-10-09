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
from typing import Optional, Any

from PyQt6.QtCore import Qt, QRectF, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QFontMetrics
from PyQt6.QtWidgets import QAbstractGraphicsShapeItem, QGraphicsSceneMouseEvent, \
    QStyleOptionGraphicsItem, QWidget, \
    QApplication, QGraphicsItem
from PyQt6.QtWidgets import QGraphicsScene
from overrides import overrides

from plotlyst.common import RELAXED_WHITE_COLOR
from plotlyst.env import app_env
from plotlyst.view.common import spawn
from plotlyst.view.common import text_color_with_bg_qcolor
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.graphics import BaseGraphicsView


class LabelItem(QAbstractGraphicsShapeItem):
    Margin: int = 0

    def __init__(self, padding: int = 5, parent=None):
        super().__init__(parent)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._padding = padding
        self._text: str = ''
        self._color: QColor = QColor('grey')
        self._font = QApplication.font()
        self._font.setPointSize(self._font.pointSize() + 1)
        self._font.setFamily(app_env.serif_font())
        self._metrics = QFontMetrics(self._font)
        self._textRect: QRect = QRect(0, 0, 1, 1)
        self._radius = 1
        self._diameter = 1
        self._recalculateRect()

    def text(self) -> str:
        return self._text

    def setText(self, text: str):
        self._text = text
        self._refresh()

    def setColor(self, color: QColor):
        self._color = color
        self.update()

    @overrides
    def boundingRect(self) -> QRectF:
        # Return the bounding rectangle of the circle
        return QRectF(0, 0, self._diameter, self._diameter)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setPen(QPen(self._color, 1))
        painter.setBrush(self._color)

        # Draw a circle centered around the text
        painter.drawEllipse(self.Margin, self.Margin, self._diameter, self._diameter)

        painter.setFont(self._font)
        text_color = text_color_with_bg_qcolor(self._color)
        painter.setPen(QPen(QColor(text_color), 1))

        # Draw the text in the center of the circle
        painter.drawText(self._textRect, Qt.AlignmentFlag.AlignCenter, self._text)

    @overrides
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            print(self.pos())
        return super().itemChange(change, value)

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        super().mouseReleaseEvent(event)
        self.setSelected(True)

    def _refresh(self):
        self._recalculateRect()
        self.prepareGeometryChange()
        self.update()

    def _recalculateRect(self):
        # Calculate the bounding rect for the text
        self._textRect = self._metrics.boundingRect(self._text)
        self._textRect.moveTopLeft(QPoint(self.Margin + self._padding, self.Margin + self._padding))

        # Calculate the diameter of the circle to fit the text
        text_width = self._textRect.width() + self._padding * 2
        text_height = self._textRect.height() + self._padding * 2
        self._diameter = max(text_width, text_height) + self.Margin * 2
        self._radius = self._diameter // 2

        # Re-center the text within the circle
        self._textRect.moveCenter(QPoint(self._radius, self._radius))


class CloverItem(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._size: int = 400
        self._icon = IconRegistry.from_name('fa5s.map-marker', 'lightgrey')
        self._color: QColor = QColor('black')

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setPen(QPen(self._color, 2))
        painter.setBrush(QColor(RELAXED_WHITE_COLOR))

        if self._icon:
            self._icon.paint(painter, 3, 3, self._size - 5, self._size - 5)

    # @overrides
    # def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     event.accept()
    #
    # @overrides
    # def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
    #     super().mouseReleaseEvent(event)


class CloverScene(QGraphicsScene):
    def __init__(self):
        super().__init__()

        self.addLabel('Horror', 163, 54, 10)
        self.addLabel('Action', 90, 83, 10)

        clover = CloverItem()
        clover.setPos(0, 0)
        self.addItem(clover)

        clover = CloverItem()
        clover.setRotation(75)
        clover.setPos(525, 112)
        self.addItem(clover)

        clover = CloverItem()
        clover.setRotation(-75)
        clover.setPos(-225, 502)
        self.addItem(clover)

        clover = CloverItem()
        clover.setRotation(145)
        clover.setPos(595, 630)
        self.addItem(clover)

        clover = CloverItem()
        clover.setRotation(-145)
        clover.setPos(140, 860)
        self.addItem(clover)

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        # event.accept()
        super().mousePressEvent(event)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        super().mouseReleaseEvent(event)

    def addLabel(self, text: str, x: int, y: int, padding: int = 5):
        item = LabelItem(padding)
        item.setText(text)
        item.setZValue(1)
        item.setPos(x, y)
        self.addItem(item)


@spawn
class View(BaseGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = CloverScene()
        self.setScene(self._scene)

        # item = LabelItem()
        # item.setText('Test label')
        # self.addItem(item)
        # 
        # clover = CloverItem()
        # clover.setPos(0, 0)
        # self.addItem(clover)
        # 
        # clover = CloverItem()
        # clover.setRotation(75)
        # clover.setPos(525, 112)
        # self.addItem(clover)
        # 
        # clover = CloverItem()
        # clover.setRotation(-75)
        # clover.setPos(-225, 502)
        # self.addItem(clover)
        # 
        # clover = CloverItem()
        # clover.setRotation(145)
        # clover.setPos(595, 630)
        # self.addItem(clover)
        # 
        # clover = CloverItem()
        # clover.setRotation(-145)
        # clover.setPos(140, 860)
        # self.addItem(clover)

        rect = self._scene.sceneRect()
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    # @overrides
    # def resizeEvent(self, event: QResizeEvent) -> None:
    #     rect = self._scene.sceneRect()
    #     rect.moveBottomRight(rect.bottomRight() + QPointF(20, 20))
    #     rect.moveTopLeft(rect.topLeft() - QPointF(20, 20))
    #     self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
