"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

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
from PyQt6.QtGui import QMouseEvent, QPainter, QColor, QPen, QFontMetrics, QFont, QIcon, QKeyEvent, \
    QResizeEvent
from PyQt6.QtWidgets import QAbstractGraphicsShapeItem, QStyleOptionGraphicsItem, \
    QWidget, QGraphicsSceneMouseEvent, QGraphicsItem, QGraphicsScene, QGraphicsSceneHoverEvent, QGraphicsLineItem, \
    QMenu, QTabWidget, QWidgetAction, QTextEdit, QToolButton
from overrides import overrides
from qtemoji import EmojiPicker
from qthandy import transparent, busy
from qthandy.filter import OpacityEventFilter

from src.main.python.plotlyst.core.domain import WorldBuildingEntity, WorldBuildingEntityType
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.common import pointy, set_tab_icon, link_buttons_to_pages, emoji_font
from src.main.python.plotlyst.view.generated.world_building_item_editor_ui import Ui_WorldBuildingItemEditor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView
from src.main.python.plotlyst.view.widget.input import TextEditBase
from src.main.python.plotlyst.view.widget.utility import ColorPicker, IconSelectorWidget

LINE_WIDTH: int = 4
DEFAULT_COLOR: str = '#219ebc'
ITEM_HORIZONTAL_DISTANCE = 20
ITEM_VERTICAL_DISTANCE = 80


class _WorldBuildingItemEditorWidget(QTabWidget, Ui_WorldBuildingItemEditor):
    def __init__(self, parent=None):
        super(_WorldBuildingItemEditorWidget, self).__init__(parent)
        self.setupUi(self)
        self._colorPicker = ColorPicker(self)
        self.wdgColorsParent.layout().addWidget(self._colorPicker)

        self._iconPicker = IconSelectorWidget(self)
        self.pageIcons.layout().addWidget(self._iconPicker)
        self._emojiPicker: Optional[EmojiPicker] = None

        self.lineName.setPlaceholderText('Entity')
        self._summary = TextEditBase(self)
        self._summary.setPlaceholderText('Summary...')
        self._summary.setMaximumHeight(75)
        self._summary.setDisabled(True)
        self.wdgSummaryParent.layout().addWidget(self._summary, alignment=Qt.AlignmentFlag.AlignTop)

        self._notes = TextEditBase(self)
        self._notes.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self._notes.setPlaceholderText('Notes...')
        self.tabNotes.layout().addWidget(self._notes)

        set_tab_icon(self, self.tabEntity, IconRegistry.world_building_icon())
        set_tab_icon(self, self.tabStyle, IconRegistry.from_name('fa5s.palette'))
        set_tab_icon(self, self.tabIcons, IconRegistry.icons_icon())
        set_tab_icon(self, self.tabNotes, IconRegistry.document_edition_icon())

        self.btnEntity.setIcon(IconRegistry.world_building_icon())
        self.btnLocation.setIcon(IconRegistry.location_icon())
        self.btnGroup.setIcon(IconRegistry.conflict_society_icon())
        self.btnItem.setIcon(IconRegistry.from_name('mdi.ring'))

        self.setCurrentWidget(self.tabEntity)

        link_buttons_to_pages(self.stackedWidget,
                              [(self.btnIconSelector, self.pageIcons), (self.btnEmojiSelector, self.pageEmojis)])

        self._item: Optional['WorldBuildingItem'] = None
        self.lineName.textEdited.connect(self._nameEdited)
        self._summary.textChanged.connect(self._summaryChanged)
        self._notes.textChanged.connect(self._notesChanged)
        self._iconPicker.iconSelected.connect(self._iconSelected)
        self._colorPicker.colorPicked.connect(self._bgColorSelected)
        self.btnGroupType.buttonClicked.connect(self._typeChanged)
        self.btnEmojiSelector.clicked.connect(self._emojiSelectorClicked)

    def setItem(self, item: 'WorldBuildingItem'):
        self._item = None
        entity = item.entity()

        self.lineName.setText(entity.name)
        self.lineName.setFocus()

        self._summary.setText(entity.summary)
        self._notes.setMarkdown(entity.notes)

        self._iconPicker.setColor(QColor(item.entity().icon_color))
        self._item = item

    @overrides
    def mousePressEvent(self, a0: QMouseEvent) -> None:
        pass

    def _nameEdited(self, text: str):
        if self._item is not None and text:
            self._item.setText(text)
            self._emit()

    def _summaryChanged(self):
        if self._item is not None:
            self._item.entity().summary = self._summary.toPlainText()
            self._emit()

    def _notesChanged(self):
        if self._item is not None:
            self._item.entity().notes = self._notes.toMarkdown()
            self._emit()

    def _iconSelected(self, icon: str, color: QColor):
        if self._item is not None:
            self._item.setIcon(icon, color.name())
            self._emit()

    def _bgColorSelected(self, color: QColor):
        if self._item is not None:
            self._item.setBackgroundColor(color)
            self._emit()

    def _typeChanged(self):
        if self._item is not None:
            if self.btnEntity.isChecked():
                self._item.setWorldBuildingType(WorldBuildingEntityType.ABSTRACT)
            elif self.btnLocation.isChecked():
                self._item.setWorldBuildingType(WorldBuildingEntityType.SETTING)
            elif self.btnGroup.isChecked():
                self._item.setWorldBuildingType(WorldBuildingEntityType.GROUP)
            elif self.btnItem.isChecked():
                self._item.setWorldBuildingType(WorldBuildingEntityType.ITEM)

            self._emit()

    @busy
    def _emojiSelectorClicked(self, _: bool):
        if self._emojiPicker is None:
            self._emojiPicker = EmojiPicker()
            self.pageEmojis.layout().addWidget(self._emojiPicker)
            self._emojiPicker.emojiPicked.connect(self._emojiPicked)

    def _emojiPicked(self, emoji: str):
        if self._item is not None:
            self._item.setEmoji(emoji)
            self._emit()

    def _emit(self):
        self._item.worldBuildingScene().modelChanged.emit()


class WorldBuildingItemEditor(QMenu):
    def __init__(self, parent=None):
        super(WorldBuildingItemEditor, self).__init__(parent)

        action = QWidgetAction(self)
        self._itemEditor = _WorldBuildingItemEditorWidget()
        action.setDefaultWidget(self._itemEditor)
        self.addAction(action)

    def edit(self, item: 'WorldBuildingItem', newItem: bool, pos: QPoint):
        self._itemEditor.setItem(item)
        if newItem:
            self._itemEditor.setCurrentWidget(self._itemEditor.tabEntity)
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
        self.setToolTip('Edit item')

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, 20, 20)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
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
        color = parent.connectorColor()
        self.setPen(QPen(color, LINE_WIDTH))
        self.setBrush(color)
        pointy(self)

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, self._size + LINE_WIDTH * 2, self._size + LINE_WIDTH * 2)

    def radius(self) -> float:
        return self.boundingRect().height() / 2

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setPen(self.pen())
        painter.drawEllipse(0, 0, self._size, self._size)
        if not self._toggled:
            painter.setBrush(self.brush())
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

    def __init__(self, entity: WorldBuildingEntity, font: QFont, emoji_font: QFont, parent: 'WorldBuildingItemGroup'):
        super(WorldBuildingItem, self).__init__(parent)
        self._entity = entity
        self._parent = parent
        self._font = font
        self._emoji_font = emoji_font

        if entity.icon_color:
            self._textColor = entity.icon_color
        elif entity.bg_color:
            self._textColor = 'white'
        else:
            self._textColor = 'black'

        self._icon: Optional[QIcon] = None
        if entity.icon:
            self._icon = IconRegistry.from_name(entity.icon, self._textColor)
        self._iconLeftMargin = 13
        self._iconSize = 25
        self._icon_y = 0
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
        return self._entity.name if self._entity.name else 'Entity'

    def setText(self, text: str):
        self._entity.name = text
        self._recalculateRect()
        self.prepareGeometryChange()
        self._parent.rearrangeItems()
        self.update()

    def worldBuildingType(self) -> WorldBuildingEntityType:
        return self._entity.type

    def setWorldBuildingType(self, type_: WorldBuildingEntityType):
        self._entity.type = type_
        self._parent.update()

    def setIcon(self, icon: str, color: str):
        self._entity.icon = icon
        self._entity.icon_color = color
        self._entity.emoji = ''
        self._icon = IconRegistry.from_name(icon, color)
        self._recalculateRect()
        self.prepareGeometryChange()
        self._parent.rearrangeItems()
        self.update()

    def setEmoji(self, emoji: str):
        self._entity.emoji = emoji
        self._icon = None
        self._entity.icon = ''
        self._entity.icon_color = ''

        self._recalculateRect()
        self.prepareGeometryChange()
        self._parent.rearrangeItems()
        self.update()

    def setBackgroundColor(self, color: QColor):
        self._entity.bg_color = color.name()
        if self._entity.icon_color:
            self._textColor = self._entity.icon_color
        elif self._entity.bg_color:
            self._textColor = 'white'
        else:
            self._textColor = 'black'

        self.update()
        self._parent.propagateColor()

    @overrides
    def update(self, rect: QRectF = ...) -> None:
        self._editItem.setPos(self._rect.x() + self._rect.width() - 20, self._rect.y() - 5)
        self._editItem.setVisible(False)
        super(WorldBuildingItem, self).update()

    def _recalculateRect(self):
        self._textRect = self._metrics.boundingRect(self.text())
        self._textRect.moveTopLeft(QPoint(0, 0))

        margins = 10
        icon_diff = self._textRect.height() + self._iconLeftMargin if self._icon or self._entity.emoji else 0

        self._rect = QRect(0, 0, self._textRect.width() + margins * 2 + icon_diff + self._penWidth * 2,
                           self._textRect.height() + margins + self._penWidth * 2)

        self._textRect.moveLeft(margins + icon_diff)

        self._iconSize = self._textRect.height()
        self._icon_y = margins / 2

    @overrides
    def boundingRect(self):
        return QRectF(self._rect)

    def width(self) -> float:
        return self.boundingRect().width()

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.black, self._penWidth, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self._rect, 2, 2)

        if self._entity.bg_color:
            painter.setBrush(QColor(self._entity.bg_color))
            pen = QPen(QColor(self._entity.bg_color), self._penWidth)
            painter.setPen(pen)
            painter.drawRoundedRect(self._rect, 25, 25)

        painter.setPen(QColor(self._textColor))
        painter.setFont(self._font)
        painter.drawText(self._textRect.x(), self._textRect.height(), self.text())
        if self._icon:
            self._icon.paint(painter, self._iconLeftMargin, self._icon_y, self._iconSize, self._iconSize)
        elif self._entity.emoji:
            painter.setFont(self._emoji_font)
            painter.drawText(self._iconLeftMargin, self._textRect.height(), self._entity.emoji)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.setSelected(True)

    @overrides
    def mouseDoubleClickEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.scene().editItem(self)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._editItem.setVisible(True)
        self._parent.setPlusVisible(True)

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._editItem.setVisible(False)

    def worldBuildingScene(self) -> Optional['WorldBuildingEditorScene']:
        scene = self.scene()
        if scene is not None and isinstance(scene, WorldBuildingEditorScene):
            return scene


class WorldBuildingItemGroup(QAbstractGraphicsShapeItem):
    def __init__(self, entity: WorldBuildingEntity, font: QFont, emoji_font: QFont, parent=None):
        super(WorldBuildingItemGroup, self).__init__(parent)
        self._entity = entity
        self._childrenEntityItems: List['WorldBuildingItemGroup'] = []
        self._inputConnector: Optional[ConnectorItem] = None
        self._outputConnectors: List[ConnectorItem] = []

        self._collapseDistance = 10
        self._font = font
        self._emoji_font = emoji_font

        self._item = WorldBuildingItem(self._entity, self._font, self._emoji_font, parent=self)
        self._item.setPos(0, 0)

        self._plusItem = PlusItem(parent=self)
        self._collapseItem = CollapseItem(parent=self)
        self._lineItem = QGraphicsLineItem(parent=self)
        self._lineItem.setPen(QPen(self.connectorColor(), LINE_WIDTH))
        self.rearrangeItems()
        self.setAcceptHoverEvents(True)

        for child_entity in self._entity.children:
            self._addChild(child_entity)
        self._updateCollapse()

    def childrenEntityItems(self) -> List['WorldBuildingItemGroup']:
        return self._childrenEntityItems

    def rearrangeChildrenItems(self):
        number = len(self.childrenEntityItems())
        if number == 0:
            return

        if number == 1:
            self._arrangeChild(self.childrenEntityItems()[0], 0)
        else:
            distances = []
            diff_ = number // 2
            if number % 2 == 0:
                for i in range(-number + diff_, number - diff_):
                    distances.append(ITEM_VERTICAL_DISTANCE * i + ITEM_VERTICAL_DISTANCE / 2)
            else:
                for i in range(-number + diff_ + 1, number - diff_):
                    distances.append(ITEM_VERTICAL_DISTANCE * i)
            for i, child in enumerate(self.childrenEntityItems()):
                self._arrangeChild(child, distances[i])

        for child in self.childrenEntityItems():
            child.rearrangeChildrenItems()

    def _arrangeChild(self, child: 'WorldBuildingItemGroup', y: float):
        child.setPos(self.boundingRect().width() + ITEM_HORIZONTAL_DISTANCE, y)
        if child.inputConnector() is None:
            ConnectorItem(self, child)
            child.setParentItem(self)
        else:
            child.inputConnector().rearrange()

        child.checkCollision()

    def checkCollision(self):
        colliding = [x for x in self.collidingItems(Qt.ItemSelectionMode.IntersectsItemBoundingRect) if
                     isinstance(x, WorldBuildingItemGroup)]
        if colliding:
            for col in colliding:
                overlap_y = (self.mapRectToScene(self.boundingRect()).topLeft() - col.mapRectToScene(
                    col.boundingRect()).topLeft()).y()
                if abs(overlap_y) > 70:
                    continue
                intersect = self.mapRectToScene(self.boundingRect()).intersected(
                    col.mapRectToScene(col.boundingRect())).height()
                common_ancestor = self.commonAncestorItem(col)
                print('------')
                print(f'{overlap_y} {intersect}')
                print(
                    f'{self.entity().name} collides with {col.entity().name}, parent {common_ancestor.entity().name}')
                shift = intersect if intersect > 1 else abs(overlap_y)
                common_ancestor.moveChildren(shift)

        for child in self.childrenEntityItems():
            child.checkCollision()

    def moveChildren(self, overlap: float):
        for child in self.childrenEntityItems():
            if child.pos().y() > 0:
                child.moveBy(0, overlap / len(self.childrenEntityItems()))
            elif child.pos().y() < 0:
                child.moveBy(0, -overlap / len(self.childrenEntityItems()))
            child.inputConnector().rearrange()

        for child in self.childrenEntityItems():
            child.checkCollision()

    def rearrangeItems(self) -> None:
        self._plusItem.setPos(self._item.boundingRect().x() + self._item.boundingRect().width() + 20,
                              self._item.boundingRect().y() + 10)
        self._plusItem.setVisible(False)
        self._updateCollapse()
        self.rearrangeChildrenItems()
        for connector in self._outputConnectors:
            connector.updatePos()

    def entity(self) -> WorldBuildingEntity:
        return self._entity

    def entityItem(self) -> WorldBuildingItem:
        return self._item

    def collapseItem(self) -> CollapseItem:
        return self._collapseItem

    def setPlusVisible(self, visible: bool):
        self._plusItem.setVisible(visible)

    def _updateCollapse(self):
        if self._childrenEntityItems:
            self._collapseItem.setVisible(True)
            self._lineItem.setVisible(True)
            self._collapseItem.setPos(self._item.width() + self._collapseDistance,
                                      self._item.boundingRect().center().y() - self._collapseItem.radius() + LINE_WIDTH)
            line_y = self._collapseItem.y() + self._collapseItem.radius() - LINE_WIDTH
            self._lineItem.setLine(self._item.width(), line_y, self._collapseItem.pos().x(), line_y)
        else:
            self._collapseItem.setVisible(False)
            self._lineItem.setVisible(False)

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._plusItem.setVisible(False)

    @overrides
    def boundingRect(self):
        rect_f = QRectF(self._item.boundingRect())
        rect_f.setWidth(rect_f.width() + self._collapseDistance + self._collapseItem.boundingRect().width())
        rect_f.setHeight(rect_f.height() + 35)
        return rect_f

    def width(self) -> float:
        return self.boundingRect().width()

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self._entity.type == WorldBuildingEntityType.ABSTRACT:
            return
        if self._entity.type == WorldBuildingEntityType.SETTING:
            icon = IconRegistry.location_icon('red')
        elif self._entity.type == WorldBuildingEntityType.GROUP:
            icon = IconRegistry.conflict_society_icon()
        else:
            icon = IconRegistry.from_name('mdi.ring')
        icon.paint(painter, self._item.boundingRect().width() - 2, 2, 10, 10)

    def addNewChild(self):
        entity = WorldBuildingEntity('')
        self._entity.children.append(entity)
        group = self._addChild(entity)

        self._updateCollapse()
        self.rearrangeChildrenItems()
        self.worldBuildingScene().modelChanged.emit()

        self.worldBuildingScene().editItem(group.entityItem(), newItem=True)

    def _addChild(self, entity: WorldBuildingEntity) -> 'WorldBuildingItemGroup':
        item = WorldBuildingItemGroup(entity, self._font, self._emoji_font)
        self._childrenEntityItems.append(item)

        return item

    def removeChild(self, child: 'WorldBuildingItemGroup'):
        if child in self._childrenEntityItems:
            self._childrenEntityItems.remove(child)
            self._entity.children.remove(child.entity())
            self._updateCollapse()
            self.worldBuildingScene().modelChanged.emit()

    def addOutputConnector(self, connector: ConnectorItem):
        self._outputConnectors.append(connector)

    def inputConnector(self) -> Optional[ConnectorItem]:
        return self._inputConnector

    def setInputConnector(self, connector: ConnectorItem):
        self._inputConnector = connector

    def connectorColor(self) -> QColor:
        if self._entity.bg_color:
            return QColor(self._entity.bg_color)
        elif self._inputConnector:
            return self._inputConnector.pen().color()
        else:
            return QColor(DEFAULT_COLOR)

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

    def propagateColor(self, color: Optional[QColor] = None):
        if color and self._entity.bg_color:
            return
        if color is None:
            if self._entity.bg_color:
                color = QColor(self._entity.bg_color)
            else:
                return

        if self._inputConnector:
            self._inputConnector.setPen(QPen(QColor(color), LINE_WIDTH))
        self._lineItem.setPen(QPen(QColor(color), LINE_WIDTH))
        self._collapseItem.setPen(QPen(QColor(color), LINE_WIDTH))

        for child in self._childrenEntityItems:
            child.propagateColor(color)


class WorldBuildingEditorScene(QGraphicsScene):
    editItemRequested = pyqtSignal(WorldBuildingItem, bool)
    itemSelected = pyqtSignal(WorldBuildingItem)
    selectionCleared = pyqtSignal()
    modelChanged = pyqtSignal()

    def __init__(self, entity: WorldBuildingEntity, parent=None):
        super(WorldBuildingEditorScene, self).__init__(parent)
        self._root = entity
        self._itemHorizontalDistance = 20
        self._itemVerticalDistance = 80

        font_size = 12
        _font = QFont('Helvetica', font_size)
        _metrics = QFontMetrics(_font)
        while _metrics.boundingRect('I').height() < 25:
            font_size += 1
            _font = QFont('Helvetica', font_size)
            _metrics = QFontMetrics(_font)

        _emoji_font = emoji_font()
        _metrics = QFontMetrics(_emoji_font)
        if app_env.is_mac():
            threshold = 35
        else:
            threshold = 25
        while _metrics.boundingRect('🙂').height() < threshold:
            _emoji_font.setPointSize(_emoji_font.pointSize() + 1)

            _metrics = QFontMetrics(_emoji_font)

        self._rootItem = WorldBuildingItemGroup(self._root, _font, _emoji_font)
        self._rootItem.setPos(0, 0)
        self.addItem(self._rootItem)

        self._rootItem.rearrangeChildrenItems()

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
                    # self._rootItem.rearrangeChildrenItems()
        elif event.key() == Qt.Key.Key_E and len(self.selectedItems()) == 1:
            item = self.selectedItems()[0]
            if isinstance(item, WorldBuildingItem):
                self.editItem(item)

    def editItem(self, item: WorldBuildingItem, newItem: bool = False):
        self.editItemRequested.emit(item, newItem)


class WorldBuildingEditor(BaseGraphicsView):
    def __init__(self, entity: WorldBuildingEntity, parent=None):
        super(WorldBuildingEditor, self).__init__(parent)

        self._scene = WorldBuildingEditorScene(entity)
        self.setScene(self._scene)
        self._scene.editItemRequested.connect(self._editItem)

        self._itemEditor = WorldBuildingItemEditor(self)

        self._btnZoomIn = QToolButton(self)
        self._btnZoomOut = QToolButton(self)
        self._btnZoomIn.setIcon(IconRegistry.plus_circle_icon('grey'))
        self._btnZoomOut.setIcon(IconRegistry.minus_icon('grey'))
        for btn_ in [self._btnZoomIn, self._btnZoomOut]:
            pointy(btn_)
            transparent(btn_)
            btn_.installEventFilter(OpacityEventFilter(btn_))
        self._btnZoomIn.clicked.connect(lambda: self.scale(1.1, 1.1))
        self._btnZoomOut.clicked.connect(lambda: self.scale(0.9, 0.9))
        self.__arrangeZoomButtons()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super(WorldBuildingEditor, self).resizeEvent(event)
        self.__arrangeZoomButtons()

    def _editItem(self, item: WorldBuildingItem, newItem: bool):
        view_pos = self.mapFromScene(item.sceneBoundingRect().topRight())
        self._itemEditor.edit(item, newItem, self.mapToGlobal(view_pos))

    def __arrangeZoomButtons(self):
        self._btnZoomOut.setGeometry(10, self.height() - 30, 20, 20)
        self._btnZoomIn.setGeometry(35, self.height() - 30, 20, 20)
