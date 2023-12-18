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
from typing import Optional

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPixmap, QShowEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem
from overrides import overrides
from qthandy import busy

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView


class WorldBuildingMapScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)

    @busy
    def loadMap(self) -> Optional[QGraphicsPixmapItem]:
        item = QGraphicsPixmapItem()
        item.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        item.setPixmap(QPixmap('/home/zkovari/Documents/map.jpg'))
        self.addItem(item)

        return item


class WorldBuildingMapView(BaseGraphicsView):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._shown = False
        self._bgItem: Optional[QGraphicsPixmapItem] = None

        self.setBackgroundBrush(QColor('#F2F2F2'))
        self._scene = WorldBuildingMapScene()
        self.setScene(self._scene)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if not self._shown:
            self._shown = True
            self._bgItem = self._scene.loadMap()
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
