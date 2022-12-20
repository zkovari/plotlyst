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

from PyQt6.QtCore import QRectF, pyqtSignal
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget, QGraphicsScene, QAbstractGraphicsShapeItem, \
    QStyleOptionGraphicsItem, QGraphicsPathItem, QGraphicsItem
from overrides import overrides
from qttoolbox import ToolBox

from src.main.python.plotlyst.core.domain import Character, Novel, RelationsNetwork
from src.main.python.plotlyst.view.icons import avatars, IconRegistry
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView


class CharacterItem(QAbstractGraphicsShapeItem):
    def __init__(self, character: Character, parent=None):
        super(CharacterItem, self).__init__(parent)
        self._character = character
        self._size: int = 128
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def character(self) -> Character:
        return self._character

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        avatar = avatars.avatar(self._character)
        avatar.paint(painter, 0, 0, self._size, self._size)


class RelationItem(QGraphicsPathItem):
    def __init__(self, source: CharacterItem, target: CharacterItem):
        super(RelationItem, self).__init__(source)


class RelationsEditorScene(QGraphicsScene):
    def __init__(self, novel: Novel, parent=None):
        super(RelationsEditorScene, self).__init__(parent)
        self._novel = novel


class RelationsView(BaseGraphicsView):
    def __init__(self, novel: Novel, parent=None):
        super(RelationsView, self).__init__(parent)
        self._novel = novel
        self._scene = RelationsEditorScene(self._novel)
        self.setScene(self._scene)
        self.scale(0.6, 0.6)

    def refresh(self, network: RelationsNetwork):
        self._scene.clear()
        for node in network.nodes:
            item = CharacterItem(node.character(self._novel))
            self._scene.addItem(item)
            item.setPos(node.x, node.y)

        self.centerOn(0, 0)


class NetworkPanel(QWidget):
    def __init__(self, network: RelationsNetwork, parent=None):
        super(NetworkPanel, self).__init__(parent)
        self._network = network

    def network(self) -> RelationsNetwork:
        return self._network


class RelationsSelectorBox(ToolBox):
    relationsSelected = pyqtSignal(RelationsNetwork)

    def __init__(self, novel: Novel, parent=None):
        super(RelationsSelectorBox, self).__init__(parent)
        self._novel = novel

    def addNetwork(self, network: RelationsNetwork):
        wdg = NetworkPanel(network)
        self.addItem(wdg, network.title, icon=IconRegistry.from_name(network.icon, network.icon_color))
