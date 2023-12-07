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
import random

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPen, QPainterPath, QBrush
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QGraphicsView, QGraphicsPixmapItem, QWidget, \
    QGraphicsPathItem
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView

SPRAY_PARTICLES = 1000
SPRAY_DIAMETER = 10


class MapCanvas(QGraphicsPixmapItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._paintMode = False

        # self._pixmap = QPixmap(800, 600)
        self._pixmap = QPixmap(resource_registry.sea_texture)
        # self._pixmap.fill(QColor('gray'))
        self.setPixmap(self._pixmap)

        self.setAcceptHoverEvents(True)

    @overrides
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        # self._paintMode = True
        pass

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self._paintMode = False

    @overrides
    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self._paintMode:
            painter = QPainter(self._pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            for n in range(SPRAY_PARTICLES):
                xo = random.gauss(0, SPRAY_DIAMETER)
                yo = random.gauss(0, SPRAY_DIAMETER)

                painter.setBrush(QColor('green'))
                painter.drawEllipse(event.pos(), SPRAY_DIAMETER, SPRAY_DIAMETER)
                painter.setPen(QColor('blue'))
                painter.drawPoint(int(event.pos().x() + xo), int(event.pos().y() + yo))

            self.setPixmap(self._pixmap)


class SprayItem(QGraphicsPixmapItem):
    def __init__(self, parent=None):
        super().__init__(parent)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: QWidget) -> None:
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = painter.pen()
        p.setWidth(1)
        p.setColor(Qt.GlobalColor.red)
        painter.setPen(p)

        for n in range(SPRAY_PARTICLES):
            xo = random.gauss(0, SPRAY_DIAMETER)
            yo = random.gauss(0, SPRAY_DIAMETER)
            painter.drawPoint(int(xo), int(yo))


class WorldBuildingMapScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._paintMode = False

        map = MapCanvas()
        self.addItem(map)

        self._pathItem = QGraphicsPathItem()
        self._pathItem.setPen(QPen(QColor('white'), 2, Qt.PenStyle.DashLine))
        self._pathItem.setBrush(QColor('red'))

        self._pathItem.setBrush(QBrush(QPixmap(resource_registry.land_texture)))

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self._pathItem.setPath(QPainterPath(event.scenePos()))
        self.addItem(self._pathItem)
        self._paintMode = True
        super().mousePressEvent(event)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.removeItem(self._pathItem)
        self._paintMode = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self._paintMode:
            path = self._pathItem.path()
            path.lineTo(event.scenePos())
            self._pathItem.setPath(path)


class WorldBuildingMapView(BaseGraphicsView):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(QColor('#F2F2F2'))
        self._scene = WorldBuildingMapScene()
        self.setScene(self._scene)
