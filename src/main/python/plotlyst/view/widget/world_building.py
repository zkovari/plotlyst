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
from typing import Optional, List

from PyQt6.QtCore import Qt, QRectF, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QWheelEvent, QPainter, QColor, QPen, QFontMetrics, QFont, QIcon, QKeyEvent
from PyQt6.QtWidgets import QGraphicsView, QAbstractGraphicsShapeItem, QStyleOptionGraphicsItem, \
    QWidget, QGraphicsSceneMouseEvent, QGraphicsItem, QGraphicsScene, QGraphicsSceneHoverEvent, QGraphicsLineItem, \
    QMenu, QTabWidget, QWidgetAction
from overrides import overrides

from src.main.python.plotlyst.core.domain import WorldBuildingEntity
from src.main.python.plotlyst.view.common import pointy, set_tab_icon
from src.main.python.plotlyst.view.generated.world_building_item_editor_ui import Ui_WorldBuildingItemEditor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.input import TextEditBase
from src.main.python.plotlyst.view.widget.utility import ColorPicker, IconSelectorWidget

LINE_WIDTH: int = 4


class ConnectorItem(QGraphicsLineItem):

    def __init__(self, source: 'WorldBuildingItemGroup', target: 'WorldBuildingItemGroup'):
        super(ConnectorItem, self).__init__(source)
        self._source = source
        self._collapseItem = source.collapseItem()
        self._target = target
        self.setPen(QPen(QColor('#219ebc'), LINE_WIDTH))
        self.updatePos()
        source.addOutputConnector(self)
        target.setInputConnector(self)

    def updatePos(self):
        self.setPos(self._collapseItem.pos().x() + self._collapseItem.boundingRect().width() - LINE_WIDTH - 1,
                    self._source.boundingRect().center().y() + LINE_WIDTH / 2)
        self.rearrange()

    def rearrange(self):
        self.setLine(0, 0, self._target.pos().x() - self.pos().x(), self._target.pos().y())


class PlusItem(QAbstractGraphicsShapeItem):
    def __init__(self, parent: 'WorldBuildingItemGroup'):
        super(PlusItem, self).__init__(parent)
        self._parent = parent
        self._plusIcon = IconRegistry.plus_circle_icon('lightgrey')
        self._iconSize = 25
        self.setAcceptHoverEvents(True)
        pointy(self)

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, self._iconSize, self._iconSize)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        self._plusIcon.paint(painter, 0, 0, self._iconSize, self._iconSize)

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
        self._parent.addNewChild()


class _WorldBuildingItemEditorWidget(QTabWidget, Ui_WorldBuildingItemEditor):
    def __init__(self, parent=None):
        super(_WorldBuildingItemEditorWidget, self).__init__(parent)
        self.setupUi(self)
        self._colorPicker = ColorPicker(self)
        self.wdgColorsParent.layout().addWidget(self._colorPicker)

        self._iconPicker = IconSelectorWidget(self)
        self.tabIcons.layout().addWidget(self._iconPicker)

        self._notes = TextEditBase(self)
        self._notes.setPlaceholderText('Notes...')
        self.tabNotes.layout().addWidget(self._notes)

        set_tab_icon(self, self.tabMain, IconRegistry.edit_icon())
        set_tab_icon(self, self.tabIcons, IconRegistry.icons_icon())
        set_tab_icon(self, self.tabNotes, IconRegistry.document_edition_icon())

        self.setCurrentWidget(self.tabMain)

        self._item: Optional['WorldBuildingItem'] = None
        self.lineName.textEdited.connect(self._nameEdited)

    def setItem(self, item: 'WorldBuildingItem'):
        self._item = item
        self.lineName.setText(item.text())
        self.lineName.setFocus()

        self._iconPicker.setColor(QColor(item.entity().icon_color))

    @overrides
    def mousePressEvent(self, a0: QMouseEvent) -> None:
        pass

    def _nameEdited(self, text: str):
        if self._item is None or not text:
            return
        self._item.setText(text)


class WorldBuildingItemEditor(QMenu):
    def __init__(self, parent=None):
        super(WorldBuildingItemEditor, self).__init__(parent)

        action = QWidgetAction(self)
        self._itemEditor = _WorldBuildingItemEditorWidget()
        action.setDefaultWidget(self._itemEditor)
        self.addAction(action)

    def edit(self, item: 'WorldBuildingItem', pos: QPoint):
        self._itemEditor.setItem(item)
        self.popup(pos)


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
        self.scene().editItem(self._parent)


class CollapseItem(QAbstractGraphicsShapeItem):
    def __init__(self, parent: 'WorldBuildingItemGroup'):
        super(CollapseItem, self).__init__(parent)
        self._parent = parent
        self._size = 15
        self._toggled = True
        pointy(self)

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, self._size + LINE_WIDTH * 2, self._size + LINE_WIDTH * 2)

    def radius(self) -> float:
        return self.boundingRect().height() / 2

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        painter.setPen(QPen(QColor('#219ebc'), LINE_WIDTH))
        painter.drawEllipse(0, 0, self._size, self._size)
        if not self._toggled:
            painter.setBrush(QColor('#219ebc'))
            painter.drawEllipse(6, 6, 3, 3)

    @overrides
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        event.accept()

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self._toggled = not self._toggled
        self._parent.setChildrenVisible(self._toggled)
        self.update()


class WorldBuildingItem(QAbstractGraphicsShapeItem):

    def __init__(self, entity: WorldBuildingEntity, parent: 'WorldBuildingItemGroup'):
        super(WorldBuildingItem, self).__init__(parent)
        self._entity = entity
        self._parent = parent

        if entity.icon_color:
            self._textColor = entity.icon_color
        elif entity.bg_color:
            self._textColor = 'white'
        else:
            self._textColor = 'black'

        self._icon: Optional[QIcon] = None
        if entity.icon:
            self._icon = IconRegistry.from_name(entity.icon, self._textColor)
        self._iconSize = 25
        self._iconLeftMargin = 13
        self._font = QFont('Helvetica', 14)
        self._metrics = QFontMetrics(self._font)
        self._rect = QRect(0, 0, 1, 1)
        self._textRect = QRect(0, 0, 1, 1)
        self._penWidth = 1
        self._recalculateRect()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self._editItem = EditItem(self)
        self.update()

    def entity(self) -> WorldBuildingEntity:
        return self._entity

    def text(self) -> str:
        return self._entity.name

    def setText(self, text: str):
        self._entity.name = text
        self._recalculateRect()
        self.prepareGeometryChange()
        self._parent.rearrangeItems()
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
        self._textRect = self._metrics.boundingRect(self.text())
        self._textRect.moveTopLeft(QPoint(0, 0))

        margins = 10
        icon_diff = self._iconSize + self._iconLeftMargin if self._icon else 0

        self._rect = QRect(0, 0, self._textRect.width() + margins + icon_diff + self._penWidth * 2,
                           self._textRect.height() + margins + self._penWidth * 2)

        self._textRect.moveLeft(margins / 2 + icon_diff)

    @overrides
    def boundingRect(self):
        return QRectF(self._rect)

    def width(self) -> float:
        return self.boundingRect().width()

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.black, self._penWidth, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self._rect, 2, 2)

        if self._entity.bg_color:
            painter.setBrush(QColor(self._entity.bg_color))
            pen = QPen(QColor('#219ebc'), self._penWidth)
            painter.setPen(pen)
            painter.drawRoundedRect(self._rect, 25, 25)

        painter.setPen(QColor(self._textColor))
        painter.setFont(self._font)
        painter.drawText(self._textRect.x(), self._textRect.height(), self.text())
        if self._icon:
            self._icon.paint(painter, self._iconLeftMargin, 8, self._iconSize, self._iconSize)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.setSelected(True)

    @overrides
    def mouseDoubleClickEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.scene().editItem(self)

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
        self._childrenEntityItems: List['WorldBuildingItemGroup'] = []
        self._inputConnector: Optional[ConnectorItem] = None
        self._outputConnectors: List[ConnectorItem] = []

        self._collapseDistance = 10

        self._item = WorldBuildingItem(self._entity, parent=self)
        self._item.setPos(0, 0)

        self._plusItem = PlusItem(parent=self)
        self._collapseItem = CollapseItem(parent=self)
        self._lineItem = QGraphicsLineItem(parent=self)
        self._lineItem.setPen(QPen(QColor('#219ebc'), LINE_WIDTH))
        self.rearrangeItems()
        self.setAcceptHoverEvents(True)

        for child_entity in self._entity.children:
            self._addChild(child_entity)
        self._updateCollapse()

    def childrenEntityItems(self) -> List['WorldBuildingItemGroup']:
        return self._childrenEntityItems

    def rearrangeItems(self) -> None:
        self._plusItem.setPos(self._item.boundingRect().x() + self._item.boundingRect().width() + 20,
                              self._item.boundingRect().y() + 10)
        self._plusItem.setVisible(False)
        self._updateCollapse()
        if self.scene():
            self.worldBuildingScene().rearrangeItems()
        for connector in self._outputConnectors:
            connector.updatePos()

    def entity(self) -> WorldBuildingEntity:
        return self._entity

    def entityItem(self) -> WorldBuildingItem:
        return self._item

    def collapseItem(self) -> CollapseItem:
        return self._collapseItem

    def _updateCollapse(self):
        if self._childrenEntityItems:
            self._collapseItem.setVisible(True)
            self._lineItem.setVisible(True)
            self._collapseItem.setPos(self._item.width() + self._collapseDistance, self._plusItem.y() + 4)
            line_y = self._collapseItem.y() + self._collapseItem.radius() - LINE_WIDTH
            self._lineItem.setLine(self._item.width(), line_y, self._collapseItem.pos().x(), line_y)
        else:
            self._collapseItem.setVisible(False)
            self._lineItem.setVisible(False)

    @overrides
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._plusItem.setVisible(True)

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._plusItem.setVisible(False)

    @overrides
    def boundingRect(self):
        rect_f = QRectF(self._item.boundingRect())
        rect_f.setWidth(rect_f.width() + self._collapseDistance + self._collapseItem.boundingRect().width())
        return rect_f

    def width(self) -> float:
        return self.boundingRect().width()

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        pass

    def addNewChild(self):
        entity = WorldBuildingEntity('Entity')
        self._entity.children.append(entity)
        self._addChild(entity)

        self._updateCollapse()
        self.worldBuildingScene().rearrangeItems()

    def _addChild(self, entity: WorldBuildingEntity) -> 'WorldBuildingItemGroup':
        item = WorldBuildingItemGroup(entity)
        self._childrenEntityItems.append(item)

        return item

    def removeChild(self, child: 'WorldBuildingItemGroup'):
        if child in self._childrenEntityItems:
            self._childrenEntityItems.remove(child)
            self._entity.children.remove(child.entity())
            self._updateCollapse()

    def addOutputConnector(self, connector: ConnectorItem):
        self._outputConnectors.append(connector)

    def inputConnector(self) -> Optional[ConnectorItem]:
        return self._inputConnector

    def setInputConnector(self, connector: ConnectorItem):
        self._inputConnector = connector

    def setChildrenVisible(self, visible: bool):
        for child in self._childrenEntityItems:
            child.setVisible(visible)

        for connector in self._outputConnectors:
            connector.setVisible(visible)

    def worldBuildingScene(self) -> Optional['WorldBuildingEditorScene']:
        scene = self.scene()
        if scene is not None and isinstance(scene, WorldBuildingEditorScene):
            return scene

    def prepareRemove(self):
        if self._inputConnector is not None:
            self.worldBuildingScene().removeItem(self._inputConnector)
            self.parentItem().removeChild(self)


class WorldBuildingEditorScene(QGraphicsScene):
    editItemRequested = pyqtSignal(WorldBuildingItem)

    def __init__(self, entity: WorldBuildingEntity, parent=None):
        super(WorldBuildingEditorScene, self).__init__(parent)
        self._root = entity
        self._itemHorizontalDistance = 20
        self._itemVerticalDistance = 80

        self._rootItem = WorldBuildingItemGroup(self._root)
        self._rootItem.setPos(0, 0)
        self.addItem(self._rootItem)

        self.rearrangeItems()

    @overrides
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        items = self.items(event.scenePos())
        if not items:
            self.clearSelection()

        super(WorldBuildingEditorScene, self).mouseReleaseEvent(event)

    @overrides
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            for item in self.selectedItems():
                if item is not self._rootItem.entityItem():
                    item.parentItem().prepareRemove()
                    self.removeItem(item.parentItem())
                    self.rearrangeItems()

    def editItem(self, item: WorldBuildingItem):
        self.editItemRequested.emit(item)

    def rearrangeItems(self):
        self.rearrangeChildrenItems(self._rootItem)

    def rearrangeChildrenItems(self, parent: WorldBuildingItemGroup):
        number = len(parent.childrenEntityItems())
        if number == 0:
            return

        if number == 1:
            self._arrangeChild(parent, parent.childrenEntityItems()[0], 0)
        else:
            distances = []
            diff_ = number // 2
            if number % 2 == 0:
                for i in range(-number + diff_, number - diff_):
                    distances.append(self._itemVerticalDistance * i + self._itemVerticalDistance / 2)
            else:
                for i in range(-number + diff_ + 1, number - diff_):
                    distances.append(self._itemVerticalDistance * i)
            for i, child in enumerate(parent.childrenEntityItems()):
                self._arrangeChild(parent, child, distances[i])

        for child in parent.childrenEntityItems():
            self.rearrangeChildrenItems(child)

    def _arrangeChild(self, parentItem: WorldBuildingItemGroup, child: WorldBuildingItemGroup, y: float):
        child.setPos(parentItem.boundingRect().width() + self._itemHorizontalDistance, y)
        if child.inputConnector() is None:
            ConnectorItem(parentItem, child)
            child.setParentItem(parentItem)
        else:
            child.inputConnector().rearrange()

        colliding = [x for x in child.collidingItems(Qt.ItemSelectionMode.IntersectsItemBoundingRect) if
                     isinstance(x, WorldBuildingItemGroup)]
        if colliding:
            for col in colliding:
                overlap = child.mapRectToScene(child.boundingRect()).intersected(
                    col.mapRectToScene(col.boundingRect())).height()
                common_ancestor = child.commonAncestorItem(col)
                self._moveChildren(common_ancestor, overlap)

    def _moveChildren(self, parent: WorldBuildingItemGroup, overlap: float):
        for child in parent.childrenEntityItems():
            if child.pos().y() >= 0:
                child.moveBy(0, overlap + self._itemVerticalDistance / 2)
            else:
                child.moveBy(0, -overlap - self._itemVerticalDistance / 2)
            child.inputConnector().rearrange()


class WorldBuildingEditor(QGraphicsView):
    def __init__(self, entity: WorldBuildingEntity, parent=None):
        super(WorldBuildingEditor, self).__init__(parent)
        self._moveOriginX = 0
        self._moveOriginY = 0

        self._scene = WorldBuildingEditorScene(entity)
        self.setScene(self._scene)
        self._scene.editItemRequested.connect(self._editItem)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

        self._itemEditor = WorldBuildingItemEditor(self)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.LeftButton:
            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()
        super(WorldBuildingEditor, self).mousePressEvent(event)

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.MiddleButton or event.buttons() & Qt.MouseButton.LeftButton:
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

    def _editItem(self, item: WorldBuildingItem):
        view_pos = self.mapFromScene(item.sceneBoundingRect().topRight())
        self._itemEditor.edit(item, self.mapToGlobal(view_pos))
