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
from typing import Optional, Any

import qtanim
from PyQt6.QtCore import Qt, QPoint, QSize, QPointF, QRectF
from PyQt6.QtGui import QColor, QPixmap, QShowEvent, QResizeEvent, QImage, QPainter
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QAbstractGraphicsShapeItem, QWidget, \
    QGraphicsSceneMouseEvent, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from overrides import overrides
from qthandy import busy
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, WorldBuildingMap
from src.main.python.plotlyst.service.image import load_image, upload_image, LoadedImage
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import tool_btn, action
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView
from src.main.python.plotlyst.view.widget.graphics.editor import ZoomBar


class MarkerItem(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__default_marker_width = 50
        self.__default_marker_height = 70
        self.__default_type_size = 25
        self._width = self.__default_marker_width
        self._height = self.__default_marker_height
        self._typeSize = self.__default_type_size

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._iconMarker = IconRegistry.from_name('fa5s.map-marker', '#ef233c')
        self._iconMarkerSelected = IconRegistry.from_name('fa5s.map-marker', '#A50C1E')
        self._iconType = IconRegistry.from_name('mdi.castle', RELAXED_WHITE_COLOR)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        if self.isSelected():
            painter.setBrush(QColor(RELAXED_WHITE_COLOR))
            # painter.drawRect(3, 3, self._width - 6, self._height - 10)
            marker = self._iconMarkerSelected
        else:
            marker = self._iconMarker
        marker.paint(painter, 0, 0, self._width, self._height)
        self._iconType.paint(painter, (self._width - self._typeSize) // 2, 15, self._typeSize, self._typeSize)

    @overrides
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        # if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
        #     self._posChangedTimer.start()
        #     self._onPosChanged()
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._onSelection(value)
        return super().itemChange(change, value)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if not self.isSelected():
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(0.9)
            self.setGraphicsEffect(effect)
            self._typeSize = self.__default_type_size + 1
            self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if not self.isSelected():
            self.setGraphicsEffect(None)
            self._typeSize = self.__default_type_size
            self.update()

    def _onSelection(self, selected: bool):
        if selected:
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(12)
            effect.setOffset(0)
            effect.setColor(QColor('white'))
            self.setGraphicsEffect(effect)

            self._typeSize = self.__default_type_size + 2
            # self.update()
        else:
            self._typeSize = self.__default_type_size
            # self.update()
            self.setGraphicsEffect(None)


class WorldBuildingMapScene(QGraphicsScene):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._map: Optional[WorldBuildingMap] = None

    def map(self) -> Optional[WorldBuildingMap]:
        return self._map

    @busy
    def loadMap(self, map: WorldBuildingMap) -> Optional[QGraphicsPixmapItem]:
        self.clear()
        image: Optional[QImage] = load_image(self._novel, map.ref)
        if image:
            self._map = map
            item = QGraphicsPixmapItem()
            item.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
            item.setPixmap(QPixmap.fromImage(image))
            self.addItem(item)

            return item
        else:
            self._map = None

    @overrides
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._map:
            self._addMarker(event.scenePos())

    def _addMarker(self, pos: QPointF):
        marker = MarkerItem()
        rect = marker.boundingRect()
        marker.setPos(pos - QPointF(rect.width() / 2, rect.height()))
        self.addItem(marker)

        self._anim = qtanim.fade_in(marker)


class WorldBuildingMapView(BaseGraphicsView):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._shown = False
        self._bgItem: Optional[QGraphicsPixmapItem] = None

        self._wdgZoomBar = ZoomBar(self)
        self._wdgZoomBar.zoomed.connect(self._scale)

        self._btnEdit = tool_btn(IconRegistry.plus_edit_icon(PLOTLYST_SECONDARY_COLOR), parent=self)
        self._btnEdit.installEventFilter(OpacityEventFilter(self._btnEdit, 0.8, 0.5))
        self._btnEdit.setIconSize(QSize(48, 48))
        self._btnEdit.setStyleSheet(f'''
        QToolButton {{
            border: 2px solid {PLOTLYST_SECONDARY_COLOR};
            border-radius: 36px;
            background: {RELAXED_WHITE_COLOR};
            padding: 10px;
        }}
        ''')

        self._menuEdit = MenuWidget(self._btnEdit)
        self._menuEdit.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        self._menuEdit.aboutToShow.connect(self._fillUpEditMenu)

        self.setBackgroundBrush(QColor('#F2F2F2'))
        self._scene = WorldBuildingMapScene(self._novel)
        self.setScene(self._scene)

        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if not self._shown:
            self._shown = True
            if self._novel.world.maps:
                map = self._novel.world.maps[0]
                self._loadMap(self._novel.world.maps[0])
                self._bgItem = self._scene.loadMap(map)
                if self._bgItem:
                    # call to calculate rect size
                    _ = self._scene.sceneRect()
                    self.centerOn(self._bgItem)

    @overrides
    def itemAt(self, pos: QPoint) -> QGraphicsItem:
        item = super().itemAt(pos)
        if self._bgItem and item is self._bgItem:
            return None

        return item

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._arrangeSideBars()

    @overrides
    def _scale(self, scale: float):
        super()._scale(scale)
        self._wdgZoomBar.updateScaledFactor(self.scaledFactor())

    def _arrangeSideBars(self):
        self._wdgZoomBar.setGeometry(10, self.height() - self._wdgZoomBar.sizeHint().height() - 25,
                                     self._wdgZoomBar.sizeHint().width(),
                                     self._wdgZoomBar.sizeHint().height())
        self._btnEdit.setGeometry(self.width() - self._btnEdit.sizeHint().width() - 20,
                                  self.height() - self._btnEdit.sizeHint().height() - 20,
                                  self._btnEdit.sizeHint().width(),
                                  self._btnEdit.sizeHint().height())

    def _loadMap(self, map: WorldBuildingMap):
        self._bgItem = self._scene.loadMap(map)
        if self._bgItem:
            # call to calculate rect size
            _ = self._scene.sceneRect()
            self.centerOn(self._bgItem)

    def _addNewMap(self):
        loadedImage: Optional[LoadedImage] = upload_image(self._novel)
        if loadedImage:
            self._novel.world.maps.clear()
            map = WorldBuildingMap(loadedImage.ref)
            self._novel.world.maps.append(map)
            self._scene.loadMap(map)
            self._loadMap(map)
            self.repo.update_world(self._novel)

    def _fillUpEditMenu(self):
        self._menuEdit.clear()
        addAction = action('Add map', IconRegistry.plus_icon(), tooltip="Upload a picture for your map",
                           slot=self._addNewMap)
        if self._scene.map():
            addAction.setText('Add another map')
        self._menuEdit.addAction(addAction)
