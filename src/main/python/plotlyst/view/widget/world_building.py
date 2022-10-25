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
from PyQt6.QtGui import QMouseEvent, QWheelEvent, QPainter, QColor, QPen, QFontMetrics, QFont, QIcon
from PyQt6.QtWidgets import QGraphicsView, QAbstractGraphicsShapeItem, QStyleOptionGraphicsItem, \
    QWidget, QGraphicsSceneMouseEvent, QGraphicsItem, QGraphicsScene, QGraphicsSceneHoverEvent
from overrides import overrides

from src.main.python.plotlyst.view.icons import IconRegistry


class PlusItem(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super(PlusItem, self).__init__(parent)
        self._plusIcon = IconRegistry.plus_circle_icon('lightgrey')
        self.setAcceptHoverEvents(True)

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, 25, 25)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        self._plusIcon.paint(painter, 0, 0, 25, 25)


class WorldBuildingItem(QAbstractGraphicsShapeItem):

    def __init__(self, parent=None):
        super(WorldBuildingItem, self).__init__(parent)
        self._text = 'My new world'
        self._icon: Optional[QIcon] = None
        self._font = QFont('Helvetica', 14)
        self._metrics = QFontMetrics(self._font)
        self._rect = QRect(0, 0, 1, 1)
        self._recalculateRect()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

    def setText(self, text: str):
        self._text = text
        self._recalculateRect()
        self.update()

    def setIcon(self, icon: QIcon):
        self._icon = icon
        self._recalculateRect()
        self.update()

    def _recalculateRect(self):
        self._rect = self._metrics.boundingRect(self._text)
        x_diff = 10
        icon_diff = 40 if self._icon else 0
        self._rect.setX(self._rect.x() - x_diff - icon_diff)
        self._rect.setWidth(self._rect.width() + x_diff)
        self._rect.setY(self._rect.y() - 5)
        self._rect.setHeight(self._rect.height() + 10)

    @overrides
    def boundingRect(self):
        return QRectF(self._rect)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self._rect, 2, 2)

        painter.setBrush(QColor('#219ebc'))
        pen = QPen(QColor('#219ebc'), 1)
        painter.setPen(pen)
        painter.drawRoundedRect(self._rect, 25, 25)

        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(self._font)
        painter.drawText(0, 0, self._text)
        if self._icon:
            self._icon.paint(painter, -30, -18, 25, 25)

    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.setSelected(True)


class WorldBuildingItemGroup(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super(WorldBuildingItemGroup, self).__init__(parent)
        self._item = WorldBuildingItem(self)
        self._item.setIcon(IconRegistry.book_icon('white'))
        self._item.setPos(0, 0)

        self._plusItem = PlusItem(self)
        self._plusItem.setPos(self._item.boundingRect().x() + self._item.boundingRect().width() + 5,
                              self._item.boundingRect().y() + 13)

        self._plusItem.setVisible(False)
        self.setAcceptHoverEvents(True)

    @overrides
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._plusItem.setVisible(True)

    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._plusItem.setVisible(False)

    @overrides
    def boundingRect(self):
        rect_f = QRectF(self._item.boundingRect())
        rect_f.setWidth(rect_f.width() + 40)
        return rect_f

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        pass


class WorldBuildingEditorScene(QGraphicsScene):

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        items = self.items(event.scenePos())
        if items:
            items[0].setSelected(True)
        else:
            self.clearSelection()


class WorldBuildingEditor(QGraphicsView):
    def __init__(self, parent=None):
        super(WorldBuildingEditor, self).__init__(parent)
        self._moveOriginX = 0
        self._moveOriginY = 0

        self._scene = WorldBuildingEditorScene()

        item = WorldBuildingItemGroup()
        item.setPos(0, 0)

        self._scene.addLine(item.boundingRect().x() + item.boundingRect().width() - 40, item.boundingRect().y() + 15,
                            400, 400, QPen(Qt.GlobalColor.red, 4))

        self._scene.addItem(item)
        item = WorldBuildingItemGroup()
        item.setPos(50, 300)
        self._scene.addItem(item)

        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()
        super(WorldBuildingEditor, self).mousePressEvent(event)

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.MiddleButton:
            oldPoint = self.mapToScene(self._moveOriginX, self._moveOriginY)
            newPoint = self.mapToScene(event.pos())
            translation = newPoint - oldPoint
            self.translate(translation.x(), translation.y())

            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()
        else:
            super(WorldBuildingEditor, self).mouseMoveEvent(event)

    @overrides
    def wheelEvent(self, event: QWheelEvent) -> None:
        super(WorldBuildingEditor, self).wheelEvent(event)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            diff = event.angleDelta().y()
            scale = (diff // 120) / 10
            self.scale(1 + scale, 1 + scale)
