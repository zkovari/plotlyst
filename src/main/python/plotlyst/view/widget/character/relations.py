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

from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget, QGraphicsScene, QAbstractGraphicsShapeItem, \
    QStyleOptionGraphicsItem, QGraphicsPathItem
from overrides import overrides

from src.main.python.plotlyst.core.domain import Character, Novel
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView


class CharacterItem(QAbstractGraphicsShapeItem):
    def __init__(self, character: Character, parent=None):
        super(CharacterItem, self).__init__(parent)
        self._character = character

    def character(self) -> Character:
        return self._character

    @overrides
    def boundingRect(self):
        pass

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        pass


class RelationItem(QGraphicsPathItem):
    def __init__(self, source: CharacterItem, target: CharacterItem):
        super(RelationItem, self).__init__(source)


class RelationsEditorScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(RelationsEditorScene, self).__init__(parent)


class RelationsView(BaseGraphicsView):
    def __init__(self, novel: Novel, parent=None):
        super(RelationsView, self).__init__(parent)
        self._novel = novel
        self._scene = RelationsEditorScene()
        self.setScene(self._scene)
