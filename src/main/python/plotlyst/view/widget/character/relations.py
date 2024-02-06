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

from typing import Optional, Set

from PyQt6.QtCore import QRectF, pyqtSignal, QSize, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget, QAbstractGraphicsShapeItem, \
    QStyleOptionGraphicsItem, QToolButton, QGraphicsObject, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent
from overrides import overrides
from qthandy import flow, transparent, pointy
from qthandy.filter import OpacityEventFilter, DragEventFilter
from qttoolbox import ToolBox

from plotlyst.core.domain import Character, Novel, Diagram
from plotlyst.view.icons import avatars, IconRegistry


class PlusItem(QAbstractGraphicsShapeItem, QGraphicsObject):
    def __init__(self, parent: 'CharacterItem'):
        super(PlusItem, self).__init__(parent)
        self._parent = parent
        self._plusIcon = IconRegistry.plus_circle_icon('lightgrey')
        self._iconSize = 25
        self.setAcceptHoverEvents(True)
        pointy(self)
        self.setToolTip('Add new relation')

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, self._iconSize, self._iconSize)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        self._plusIcon.paint(painter, 0, 0, self._iconSize, self._iconSize)

    @overrides
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._plusIcon = IconRegistry.plus_circle_icon('#457b9d')
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.relationsScene().linkMode():
            self._plusIcon = IconRegistry.plus_circle_icon('#457b9d')
        else:
            self._plusIcon = IconRegistry.plus_circle_icon('lightgrey')
        self.update()

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    def reset(self):
        self._plusIcon = IconRegistry.plus_circle_icon('lightgrey')

    def relationsScene(self) -> 'RelationsEditorScene':
        return self.scene()

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.relationsScene().startLink()


CHARACTER_AVATAR_MIME_TYPE = 'application/character-avatar'


class _CharacterSelectorAvatar(QToolButton):
    def __init__(self, character: Character, parent=None):
        super(_CharacterSelectorAvatar, self).__init__(parent)
        self._character = character
        transparent(self)
        self.setIconSize(QSize(20, 20))
        self.setIcon(avatars.avatar(character))
        self.setToolTip(character.name)
        self.installEventFilter(OpacityEventFilter(self, enterOpacity=0.8, leaveOpacity=1.0))
        self.installEventFilter(
            DragEventFilter(self, CHARACTER_AVATAR_MIME_TYPE, dataFunc=lambda wdg: character))
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def character(self) -> Character:
        return self._character


class NetworkPanel(QWidget):
    def __init__(self, novel: Novel, network: Diagram, parent=None):
        super(NetworkPanel, self).__init__(parent)
        self._novel = novel
        self._network = network

        flow(self, spacing=0)
        for character in self._novel.characters:
            avatar = _CharacterSelectorAvatar(character)
            self.layout().addWidget(avatar)

        self.updateAvatars()

    def network(self) -> Diagram:
        return self._network

    def updateAvatars(self):
        occupied_character_ids: Set[str] = set([str(x.character_id) for x in self._network.nodes])
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item.widget() and isinstance(item.widget(), _CharacterSelectorAvatar):
                wdg: _CharacterSelectorAvatar = item.widget()
                wdg.setHidden(str(wdg.character().id) in occupied_character_ids)


class RelationsSelectorBox(ToolBox):
    relationsSelected = pyqtSignal(Diagram)

    def __init__(self, novel: Novel, parent=None):
        super(RelationsSelectorBox, self).__init__(parent)
        self._novel = novel

    def addNetwork(self, network: Diagram):
        wdg = NetworkPanel(self._novel, network)
        self.addItem(wdg, network.title, icon=IconRegistry.from_name(network.icon, network.icon_color))

    def refreshCharacters(self, network: Diagram):
        panel = self.currentWidget()
        if panel.network() is network:
            panel.updateAvatars()
