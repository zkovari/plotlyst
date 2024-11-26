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
from PyQt6.QtCore import QPointF, Qt, QRectF
from PyQt6.QtWidgets import QGraphicsView, QGraphicsItem
from overrides import overrides

from plotlyst.core.domain import GraphicsItemType, Diagram, DiagramData, Novel
from plotlyst.view.common import spawn
from plotlyst.view.widget.characters import CharacterSelectorMenu
from plotlyst.view.widget.graphics import NetworkGraphicsView, NetworkScene, NodeItem, CharacterItem


class AlliesGraphicsScene(NetworkScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        diagram = Diagram('Allies')
        diagram.data = DiagramData()
        self.setDiagram(diagram)

    @overrides
    def _addNewDefaultItem(self, pos: QPointF):
        self._addNewItem(pos, GraphicsItemType.CHARACTER)

    @overrides
    def _addNewItem(self, scenePos: QPointF, itemType: GraphicsItemType, subType: str = '') -> NodeItem:
        item: CharacterItem = super()._addNewItem(scenePos, itemType, subType)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        item.setConfinedRect(QRectF(-20, -20, 340, 340))
        item.setLabelVisible(False)

        return item

    @overrides
    def _save(self):
        pass


@spawn
class AlliesGraphicsView(NetworkGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel = Novel('My novel')
        self.setRubberBandEnabled(False)
        self.setScalingEnabled(False)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setSceneRect(15, 15, 370, 370)
        self.setFixedSize(400, 400)

        self._controlsNavBar.setHidden(True)
        self._wdgZoomBar.setHidden(True)

    @overrides
    def _initScene(self) -> NetworkScene:
        return AlliesGraphicsScene()

    @overrides
    def _characterSelectorMenu(self) -> CharacterSelectorMenu:
        return CharacterSelectorMenu(self._novel, parent=self)
