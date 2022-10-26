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
    QWidget, QGraphicsSceneMouseEvent, QGraphicsItem, QGraphicsScene, QGraphicsSceneHoverEvent, QInputDialog, QLineEdit
from overrides import overrides

from src.main.python.plotlyst.core.domain import WorldBuildingEntity
from src.main.python.plotlyst.view.common import pointy
from src.main.python.plotlyst.view.icons import IconRegistry


class PlusItem(QAbstractGraphicsShapeItem):
    def __init__(self, parent: 'WorldBuildingItemGroup'):
        super(PlusItem, self).__init__(parent)
        self._parent = parent
        self._plusIcon = IconRegistry.plus_circle_icon('lightgrey')
        self.setAcceptHoverEvents(True)
        pointy(self)

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, 25, 25)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        self._plusIcon.paint(painter, 0, 0, 25, 25)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._plusIcon = IconRegistry.plus_circle_icon('#457b9d')
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._plusIcon = IconRegistry.plus_circle_icon('lightgrey')
        self.update()

    @overrides
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        event.accept()

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self._parent.addChild()


class EditItem(QAbstractGraphicsShapeItem):

    def __init__(self, parent: 'WorldBuildingItem'):
        super(EditItem, self).__init__(parent)
        self._parent = parent
        self._editIcon = IconRegistry.edit_icon('white')
        self._hovered = False
        self._pressed = False
        self.setAcceptHoverEvents(True)
        pointy(self)

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, 20, 20)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        painter.setPen(Qt.GlobalColor.white)
        if self._hovered:
            color = '#b100e8'
        else:
            color = '#7209b7'
        painter.setBrush(QColor(color))
        if self._pressed:
            painter.drawEllipse(0, 0, 19, 19)
        else:
            painter.drawEllipse(0, 0, 20, 20)
        self._editIcon.paint(painter, 1, 1, 18, 18)

    @overrides
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        event.accept()
        self._pressed = True
        self.update()

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self._pressed = False
        self.update()
        self._edit()

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = True
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = False
        self.update()

    def _edit(self):
        text, ok = QInputDialog.getText(self.scene().views()[0], 'Edit', 'Edit text', QLineEdit.EchoMode.Normal,
                                        self._parent.text())
        if ok:
            self._parent.setText(text)


class WorldBuildingItem(QAbstractGraphicsShapeItem):

    def __init__(self, entity: WorldBuildingEntity, parent):
        super(WorldBuildingItem, self).__init__(parent)
        self._entity = entity

        self._icon: Optional[QIcon] = None
        self._font = QFont('Helvetica', 14)
        self._metrics = QFontMetrics(self._font)
        self._rect = QRect(0, 0, 1, 1)
        self._recalculateRect()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self._editItem = EditItem(self)
        self.update()

    def text(self) -> str:
        return self._entity.name

    def setText(self, text: str):
        self._entity.name = text
        self._recalculateRect()
        self.prepareGeometryChange()
        self.parentItem().update()
        self.update()

    def setIcon(self, icon: QIcon):
        self._icon = icon
        self._recalculateRect()
        self.update()

    @overrides
    def update(self, rect: QRectF = ...) -> None:
        self._editItem.setPos(self._rect.x() + self._rect.width() - 20, self._rect.y() - 5)
        self._editItem.setVisible(False)
        super(WorldBuildingItem, self).update()

    def _recalculateRect(self):
        self._rect = self._metrics.boundingRect(self.text())
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
        painter.drawText(0, 0, self.text())
        if self._icon:
            self._icon.paint(painter, -30, -18, 25, 25)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.setSelected(True)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._editItem.setVisible(True)

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._editItem.setVisible(False)


class WorldBuildingItemGroup(QAbstractGraphicsShapeItem):
    def __init__(self, entity: WorldBuildingEntity, parent=None):
        super(WorldBuildingItemGroup, self).__init__(parent)
        self._entity = entity
        self._item = WorldBuildingItem(self._entity, parent=self)
        self._item.setIcon(IconRegistry.book_icon('white'))
        self._item.setPos(0, 0)

        self._plusItem = PlusItem(parent=self)
        self.update()
        self.setAcceptHoverEvents(True)

    @overrides
    def update(self, rect: QRectF = ...) -> None:
        self._plusItem.setPos(self._item.boundingRect().x() + self._item.boundingRect().width() + 10,
                              self._item.boundingRect().y() + 10)
        self._plusItem.setVisible(False)

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

    def addChild(self):
        child = WorldBuildingEntity('Entity')
        self._entity.children.append(child)
        WorldBuildingItemGroup(child, parent=self)

        self.scene().rearrangeItems()


class WorldBuildingEditorScene(QGraphicsScene):

    def __init__(self, entity: WorldBuildingEntity, parent=None):
        super(WorldBuildingEditorScene, self).__init__(parent)
        self._root = entity
        self._itemHorizontalDistance = 40

        self._rootItem = WorldBuildingItemGroup(self._root)
        self.addItem(self._rootItem)

        self.rearrangeItems()

    @overrides
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        items = self.items(event.scenePos())
        if not items:
            self.clearSelection()

        super(WorldBuildingEditorScene, self).mouseReleaseEvent(event)

    def rearrangeItems(self):
        self._rootItem.setPos(0, 0)
        for child in self._rootItem.childItems():
            if isinstance(child, WorldBuildingItemGroup):
                child.setPos(self._rootItem.boundingRect().width() + self._itemHorizontalDistance, self._rootItem.y())


class WorldBuildingEditor(QGraphicsView):
    def __init__(self, entity: WorldBuildingEntity, parent=None):
        super(WorldBuildingEditor, self).__init__(parent)
        self._moveOriginX = 0
        self._moveOriginY = 0

        self._scene = WorldBuildingEditorScene(entity)
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
