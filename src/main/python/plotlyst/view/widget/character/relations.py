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

from typing import Optional, Set, Any

import qtanim
from PyQt6.QtCore import QRectF, pyqtSignal, QSize, Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QKeyEvent
from PyQt6.QtWidgets import QWidget, QGraphicsScene, QAbstractGraphicsShapeItem, \
    QStyleOptionGraphicsItem, QGraphicsPathItem, QGraphicsItem, QToolButton, QGraphicsSceneDragDropEvent, \
    QGraphicsObject
from overrides import overrides
from qthandy import flow, transparent, pointy
from qthandy.filter import OpacityEventFilter, DragEventFilter
from qttoolbox import ToolBox

from src.main.python.plotlyst.core.domain import Character, Novel, RelationsNetwork, CharacterNode
from src.main.python.plotlyst.view.icons import avatars, IconRegistry
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView


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
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
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
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        event.accept()

    def reset(self):
        self._plusIcon = IconRegistry.plus_circle_icon('lightgrey')

    def relationsScene(self) -> 'RelationsEditorScene':
        return self.scene()

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.relationsScene().startLink()


class CharacterItem(QAbstractGraphicsShapeItem):

    def __init__(self, character: Character, node: CharacterNode, parent=None):
        super(CharacterItem, self).__init__(parent)
        self._character = character
        self._node = node
        self._size: int = 128
        self._margin: int = 25
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._posChangedTimer = QTimer()
        self._posChangedTimer.setInterval(1000)
        self._posChangedTimer.timeout.connect(self._posChangedOnTimeout)
        self._plusItem = PlusItem(self)
        self._plusItem.setPos(50, -self._margin)
        self._plusItem.setVisible(False)
        self._animation = None
        self._linkMode: bool = False

    def character(self) -> Character:
        return self._character

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, -self._margin, self._size, self._size + self._margin)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self._linkMode:
            painter.setPen(QPen(Qt.GlobalColor.darkBlue, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(0, 0, self._size, self._size, 2, 2)
        elif self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(0, 0, self._size, self._size, 2, 2)

        avatar = avatars.avatar(self._character)
        avatar.paint(painter, 0, 0, self._size, self._size)

    @overrides
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._posChangedTimer.start(1000)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._plusItem.setVisible(bool(value))
            if value:
                self._animation = qtanim.fade_in(self._plusItem)
            else:
                self.relationsScene().endLink()
                self._plusItem.reset()
        return super(CharacterItem, self).itemChange(change, value)

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.relationsScene().linkMode():
            self._linkMode = True
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._linkMode = False
        self.update()

    def relationsScene(self) -> 'RelationsEditorScene':
        return self.scene()

    def _posChangedOnTimeout(self):
        self._posChangedTimer.stop()
        self._node.x = self.scenePos().x()
        self._node.y = self.scenePos().y()


class RelationItem(QGraphicsPathItem):
    def __init__(self, source: CharacterItem, target: CharacterItem):
        super(RelationItem, self).__init__(source)


class RelationsEditorScene(QGraphicsScene):
    charactersChanged = pyqtSignal(RelationsNetwork)

    def __init__(self, novel: Novel, parent=None):
        super(RelationsEditorScene, self).__init__(parent)
        self._novel = novel
        self._network: Optional[RelationsNetwork] = None
        self._linkMode: bool = False

    def setNetwork(self, network: RelationsNetwork):
        self._network = network

    @overrides
    def dragEnterEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
        if event.mimeData().hasFormat(CHARACTER_AVATAR_MIME_TYPE):
            event.accept()

    @overrides
    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
        if event.mimeData().hasFormat(CHARACTER_AVATAR_MIME_TYPE):
            event.accept()

    @overrides
    def dropEvent(self, event: 'QGraphicsSceneDragDropEvent') -> None:
        if event.mimeData().hasFormat(CHARACTER_AVATAR_MIME_TYPE):
            event.accept()

            character: Character = event.mimeData().reference()
            node = CharacterNode(event.scenePos().x(), event.scenePos().y())
            node.set_character(character)
            self._network.nodes.append(node)

            item = CharacterItem(character, node)
            item.setPos(event.scenePos())
            self.addItem(item)
            self.charactersChanged.emit(self._network)

    @overrides
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            for item in self.selectedItems():
                if isinstance(item, CharacterItem):
                    self._network.nodes[:] = [node for node in self._network.nodes if
                                              node.character_id != item.character().id]
                    self.removeItem(item)
                    self.charactersChanged.emit(self._network)

    def linkMode(self) -> bool:
        return self._linkMode

    def startLink(self):
        self._linkMode = True

    def endLink(self):
        self._linkMode = False


class RelationsView(BaseGraphicsView):
    def __init__(self, novel: Novel, parent=None):
        super(RelationsView, self).__init__(parent)
        self._novel = novel
        self._scene = RelationsEditorScene(self._novel)
        self.setScene(self._scene)
        self.scale(0.6, 0.6)
        self.setAcceptDrops(True)

    def relationsScene(self) -> RelationsEditorScene:
        return self._scene

    def refresh(self, network: RelationsNetwork):
        self._scene.clear()
        self._scene.setNetwork(network)
        for node in network.nodes:
            item = CharacterItem(node.character(self._novel), node)
            self._scene.addItem(item)
            item.setPos(node.x, node.y)

        self.centerOn(0, 0)


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
    def __init__(self, novel: Novel, network: RelationsNetwork, parent=None):
        super(NetworkPanel, self).__init__(parent)
        self._novel = novel
        self._network = network

        flow(self, spacing=0)
        for character in self._novel.characters:
            avatar = _CharacterSelectorAvatar(character)
            self.layout().addWidget(avatar)

        self.updateAvatars()

    def network(self) -> RelationsNetwork:
        return self._network

    def updateAvatars(self):
        occupied_character_ids: Set[str] = set([str(x.character_id) for x in self._network.nodes])
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item.widget() and isinstance(item.widget(), _CharacterSelectorAvatar):
                wdg: _CharacterSelectorAvatar = item.widget()
                wdg.setHidden(str(wdg.character().id) in occupied_character_ids)


class RelationsSelectorBox(ToolBox):
    relationsSelected = pyqtSignal(RelationsNetwork)

    def __init__(self, novel: Novel, parent=None):
        super(RelationsSelectorBox, self).__init__(parent)
        self._novel = novel

    def addNetwork(self, network: RelationsNetwork):
        wdg = NetworkPanel(self._novel, network)
        self.addItem(wdg, network.title, icon=IconRegistry.from_name(network.icon, network.icon_color))

    def refreshCharacters(self, network: RelationsNetwork):
        panel = self.currentWidget()
        if panel.network() is network:
            panel.updateAvatars()
