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
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsView, QGraphicsItem, QGraphicsOpacityEffect
from overrides import overrides

from plotlyst.common import RELAXED_WHITE_COLOR
from plotlyst.core.domain import GraphicsItemType, Diagram, DiagramData, Novel, Node, DynamicPlotPrincipleGroup
from plotlyst.service.cache import entities_registry
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.widget.characters import CharacterSelectorMenu
from plotlyst.view.widget.graphics import NetworkGraphicsView, NetworkScene, NodeItem, CharacterItem, \
    PlaceholderSocketItem, ConnectorItem
from plotlyst.view.widget.graphics.items import IconItem


class AlliesGraphicsScene(NetworkScene):
    def __init__(self, novel: Novel, principleGroup: DynamicPlotPrincipleGroup, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._group = principleGroup

        self.repo = RepositoryPersistenceManager.instance()

        diagram = Diagram('Allies')
        diagram.data = DiagramData()

        for principle in self._group.principles:
            if principle.node is None:
                print('princ node is None')
                character_id = None
                if principle.character_id:
                    character = entities_registry.character(principle.character_id)
                    if character:
                        print(f'set char id{character.id}')
                        character_id = character.id
                principle.node = Node(0, 0, type=GraphicsItemType.CHARACTER, size=40, character_id=character_id)
                self._save()

            diagram.data.nodes.append(principle.node)

        self.setDiagram(diagram)

        socket1 = PlaceholderSocketItem()
        socket1.setPos(0, 200)
        socket2 = PlaceholderSocketItem()
        socket2.setPos(375, 200)
        hline = ConnectorItem(socket1, socket2)
        hline.setColor(QColor('grey'))
        hline.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        hline.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

        self.addItem(socket1)
        self.addItem(socket2)
        self.addItem(hline)

        mid = 375 // 2
        socket1 = PlaceholderSocketItem()
        socket1.setPos(mid, 385)
        socket2 = PlaceholderSocketItem()
        socket2.setPos(mid, 5)
        vline = ConnectorItem(socket1, socket2)
        vline.setColor(QColor('grey'))
        vline.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        vline.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

        self.addItem(socket1)
        self.addItem(socket2)
        self.addItem(vline)

        self.__addIcon(Node(mid - 7, -18, GraphicsItemType.ICON, icon='fa5s.thumbs-up', color='#266dd3', size=20))
        self.__addIcon(Node(mid - 7, 360, GraphicsItemType.ICON, icon='fa5s.thumbs-down', color='#9e1946', size=20))
        self.__addIcon(Node(355, 195, GraphicsItemType.ICON, icon='mdi.emoticon-happy', color='#00ca94', size=20))
        self.__addIcon(Node(-17, 195, GraphicsItemType.ICON, icon='fa5s.angry', color='#ef0000', size=20))

    @overrides
    def _addNewDefaultItem(self, pos: QPointF):
        pass

    @overrides
    def _addNode(self, node: Node) -> NodeItem:
        item = super()._addNode(node)

        if isinstance(item, CharacterItem):
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            item.setConfinedRect(QRectF(-10, -10, 320, 330))
            item.setZValue(1)
            # item.setLabelVisible(False)

        return item

    @overrides
    def _addNewItem(self, scenePos: QPointF, itemType: GraphicsItemType, subType: str = '') -> NodeItem:
        print('add new item')
        item: CharacterItem = super()._addNewItem(scenePos, itemType, subType)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        item.setConfinedRect(QRectF(-10, -10, 320, 330))
        item.setLabelVisible(False)
        item.setSize(40)

        return item

    @overrides
    def _save(self):
        self.repo.update_novel(self._novel)

    def __addIcon(self, node: Node):
        icon = IconItem(node)
        icon.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        icon.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        icon.setDoubleClickEditEnabled(False)
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(0.5)
        icon.setGraphicsEffect(effect)
        self.addItem(icon)


class AlliesGraphicsView(NetworkGraphicsView):
    def __init__(self, novel: Novel, principleGroup: DynamicPlotPrincipleGroup, parent=None):
        self._novel = novel
        self._group = principleGroup
        super().__init__(parent)
        self.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))
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
        return AlliesGraphicsScene(self._novel, self._group)

    @overrides
    def _characterSelectorMenu(self) -> CharacterSelectorMenu:
        return CharacterSelectorMenu(self._novel, parent=self)
