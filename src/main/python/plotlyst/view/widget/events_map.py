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
from enum import Enum
from typing import Optional, List

from PyQt6.QtCore import QRectF, Qt, QPointF, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QColor, QPainter, QPen, QKeyEvent, QFontMetrics
from PyQt6.QtWidgets import QGraphicsScene, QWidget, QAbstractGraphicsShapeItem, QGraphicsSceneHoverEvent, \
    QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QGraphicsTextItem, QApplication
from overrides import overrides
from qthandy import transparent
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel, Character, CharacterNode, Node
from src.main.python.plotlyst.view.common import action
from src.main.python.plotlyst.view.icons import avatars
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView, NodeItem, ConnectorItem
from src.main.python.plotlyst.view.widget.input import AutoAdjustableLineEdit


def draw_rect(painter: QPainter, item: QAbstractGraphicsShapeItem):
    painter.setPen(QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine))
    painter.drawRoundedRect(item.boundingRect(), 2, 2)


def draw_center(painter: QPainter, item: QAbstractGraphicsShapeItem):
    painter.setPen(QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine))
    painter.drawEllipse(item.boundingRect().center(), 1, 1)


def draw_zero(painter: QPainter):
    painter.setPen(QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DashLine))
    painter.drawEllipse(QPointF(0, 0), 1, 1)


def draw_helpers(painter: QPainter, item: QAbstractGraphicsShapeItem):
    draw_rect(painter, item)
    draw_center(painter, item)
    draw_zero(painter)


class ItemType(Enum):
    Event = 0


class MindMapNode(NodeItem):
    def mindMapScene(self) -> 'EventsMindMapScene':
        return self.scene()

    def linkMode(self) -> bool:
        return self.mindMapScene().linkMode()


class SocketItem(QAbstractGraphicsShapeItem):
    def __init__(self, parent: 'ConnectableNode'):
        super(SocketItem, self).__init__(parent)

        self._size = 16
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self._linkAvailable = True
        self.setToolTip('Connect')

        self._connectors: List[ConnectorItem] = []

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        if self._linkAvailable:
            painter.setPen(QPen(QColor(PLOTLYST_SECONDARY_COLOR), 2))
        else:
            painter.setPen(QPen(QColor('lightgrey'), 2))

        radius = 7 if self._hovered else 5
        painter.drawEllipse(QPointF(self._size / 2, self._size // 2), radius, radius)
        if self._hovered and self.mindMapScene().linkMode():
            painter.drawEllipse(QPointF(self._size / 2, self._size // 2), 2, 2)

    @overrides
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = True
        if self.mindMapScene().linkMode() and self.mindMapScene().linkSource().parentItem() == self.parentItem():
            self._linkAvailable = False
        else:
            self._linkAvailable = True
        self.setToolTip('Connect' if self._linkAvailable else 'Cannot connect to itself')
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = False
        self._linkAvailable = True
        self.setToolTip('Connect')
        self.update()

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    @overrides
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.mindMapScene().linkMode():
            if self.mindMapScene().linkSource().parentItem() != self.parentItem():
                self.mindMapScene().link(self)
        else:
            self.mindMapScene().startLink(self)

    def addConnector(self, connector: ConnectorItem):
        self._connectors.append(connector)

    def rearrangeConnectors(self):
        for con in self._connectors:
            con.rearrange()

    def mindMapScene(self) -> 'EventsMindMapScene':
        return self.scene()


class PlaceholderItem(SocketItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEnabled(False)
        self.setAcceptHoverEvents(False)
        self.setToolTip('Click to add a new node')


class ConnectableNode(MindMapNode):
    def __init__(self, node: Node, parent=None):
        super().__init__(node, parent)
        self._sockets: List[SocketItem] = []

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.linkMode():
            self._setSocketsVisible()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if not self.isSelected() and self.linkMode():
            self._setSocketsVisible(False)

    @overrides
    def _onPosChanged(self):
        for socket in self._sockets:
            socket.rearrangeConnectors()

    @overrides
    def _onSelection(self, selected: bool):
        self._setSocketsVisible(selected)

    def _setSocketsVisible(self, visible: bool = True):
        for socket in self._sockets:
            socket.setVisible(visible)


class EventItem(ConnectableNode):
    def __init__(self, node: Node, parent=None):
        super().__init__(node, parent)
        self._text: str = 'Type this event'
        self.setPos(node.x, node.y)

        self._margin = 30
        self._padding = 20

        self._metrics = QFontMetrics(QApplication.font())
        self._textRect: QRect = QRect(0, 0, 1, 1)
        self._width = 1
        self._height = 1
        self._nestedRectWidth = 1
        self._nestedRectHeight = 1

        self._socketLeft = SocketItem(self)
        self._socketTopLeft = SocketItem(self)
        self._socketTopCenter = SocketItem(self)
        self._socketTopRight = SocketItem(self)
        self._socketRight = SocketItem(self)
        self._socketBottomLeft = SocketItem(self)
        self._socketBottomCenter = SocketItem(self)
        self._socketBottomRight = SocketItem(self)
        self._sockets.extend([self._socketLeft,
                              self._socketTopLeft, self._socketTopCenter, self._socketTopRight,
                              self._socketRight,
                              self._socketBottomRight, self._socketBottomCenter, self._socketBottomLeft])
        self._setSocketsVisible(False)

        self._recalculateRect()

    def text(self) -> str:
        return self._text

    def setText(self, text: str):
        self._text = text
        self._recalculateRect()
        self.prepareGeometryChange()
        self.setSelected(False)
        self.update()

    def textRect(self) -> QRect:
        return self._textRect

    def textSceneRect(self) -> QRectF:
        return self.mapRectToScene(self._textRect.toRectF())

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self._margin, self._margin, self._nestedRectWidth, self._nestedRectHeight, 2, 2)

        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawText(self._textRect, Qt.AlignmentFlag.AlignCenter, self._text)
        painter.drawRoundedRect(self._margin, self._margin, self._nestedRectWidth, self._nestedRectHeight, 24, 24)

    @overrides
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.mindMapScene().editEventText(self)

    def _recalculateRect(self):
        self._textRect = self._metrics.boundingRect(self._text)
        self._textRect.moveTopLeft(QPoint(self._margin + self._padding, self._margin + self._padding))
        self._width = self._textRect.width() + self._margin * 2 + self._padding * 2
        self._height = self._textRect.height() + self._margin * 2 + self._padding * 2

        self._nestedRectWidth = self._textRect.width() + self._padding * 2
        self._nestedRectHeight = self._textRect.height() + self._padding * 2

        socketWidth = self._socketLeft.boundingRect().width()
        socketRad = socketWidth / 2
        socketPadding = (self._margin - socketWidth) / 2
        self._socketTopCenter.setPos(self._width / 2 - socketRad, socketPadding)
        self._socketTopLeft.setPos(self._nestedRectWidth / 3 - socketRad, socketPadding)
        self._socketTopRight.setPos(self._nestedRectWidth, socketPadding)
        self._socketRight.setPos(self._width - self._margin + socketPadding, self._height / 2 - socketRad)
        self._socketBottomCenter.setPos(self._width / 2 - socketRad, self._height - self._margin + socketPadding)
        self._socketBottomLeft.setPos(self._nestedRectWidth / 3 - socketRad,
                                      self._height - self._margin + socketPadding)
        self._socketBottomRight.setPos(self._nestedRectWidth, self._height - self._margin + socketPadding)
        self._socketLeft.setPos(socketPadding, self._height / 2 - socketRad)


class CharacterItem(ConnectableNode):
    def __init__(self, character: Character, node: CharacterNode, parent=None):
        super().__init__(node, parent)
        self._character = character

        self._size: int = 108
        self._margin = 30

        self._socketTop = SocketItem(self)
        self._socketRight = SocketItem(self)
        self._socketBottom = SocketItem(self)
        self._socketLeft = SocketItem(self)
        self._sockets.extend([self._socketLeft, self._socketTop, self._socketRight, self._socketBottom])
        socketWidth = self._socketTop.boundingRect().width()
        half = self._margin + (self._size - socketWidth) / 2
        padding = (self._margin - socketWidth) / 2
        self._socketTop.setPos(half, padding)
        self._socketRight.setPos(self._size + self._margin + padding, half)
        self._socketBottom.setPos(half, self._size + self._margin + padding)
        self._socketLeft.setPos(padding, half)

        self._setSocketsVisible(False)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size + self._margin * 2, self._size + self._margin * 2)

    def rightSocket(self) -> SocketItem:
        return self._socketRight

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self._margin, self._margin, self._size, self._size, 2, 2)

        avatar = avatars.avatar(self._character)
        avatar.paint(painter, self._margin, self._margin, self._size, self._size)


class TextLineEditorPopup(MenuWidget):

    def __init__(self, text: str, rect: QRect, parent=None):
        super().__init__(parent)
        transparent(self)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._lineEdit = AutoAdjustableLineEdit(defaultWidth=rect.width())
        self._lineEdit.setText(text)
        self.addWidget(self._lineEdit)

        self._lineEdit.editingFinished.connect(self.hide)

    @overrides
    def showEvent(self, QShowEvent):
        self._lineEdit.setFocus()

    def text(self) -> str:
        return self._lineEdit.text()


class EventsMindMapScene(QGraphicsScene):
    addNewNode = pyqtSignal(PlaceholderItem)
    editEvent = pyqtSignal(EventItem)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._linkMode: bool = False
        self._placeholder: Optional[PlaceholderItem] = None
        self._connectorPlaceholder: Optional[ConnectorItem] = None

        characterItem = CharacterItem(novel.characters[0], CharacterNode(50, 50))
        characterItem.setPos(50, 50)

        eventItem = EventItem(Node(400, 100))
        self.addItem(characterItem)
        self.addItem(eventItem)

    def linkMode(self) -> bool:
        return self._linkMode

    def linkSource(self) -> Optional[SocketItem]:
        if self._connectorPlaceholder is not None:
            return self._connectorPlaceholder.source()

    def startLink(self, source: SocketItem):
        self._linkMode = True
        self._placeholder = PlaceholderItem()
        self._placeholder.setVisible(False)
        self._placeholder.setEnabled(False)
        self.addItem(self._placeholder)
        self._connectorPlaceholder = ConnectorItem(source, self._placeholder)
        self.addItem(self._connectorPlaceholder)

        self._placeholder.setPos(source.scenePos())
        self._connectorPlaceholder.rearrange()

    def endLink(self):
        self._linkMode = False
        self.removeItem(self._connectorPlaceholder)
        self.removeItem(self._placeholder)
        self._connectorPlaceholder = None
        self._placeholder = None

    def link(self, target: SocketItem):
        connector = ConnectorItem(self._connectorPlaceholder.source(), target)
        self._connectorPlaceholder.source().addConnector(connector)
        target.addConnector(connector)
        self.addItem(connector)
        self.endLink()

    def editEventText(self, item: EventItem):
        self.editEvent.emit(item)

    def addNewItem(self, pos: QPointF, itemType: ItemType):
        if itemType == ItemType.Event:
            item = QGraphicsTextItem('Type')
        else:
            return

        item.setPos(pos)
        connector = ConnectorItem(self._connectorPlaceholder.source(), item)
        self.addItem(item)
        self.addItem(connector)

        self.endLink()

    @overrides
    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            self._placeholder.setPos(event.scenePos())
            self._connectorPlaceholder.rearrange()
        super().mouseMoveEvent(event)

    @overrides
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            if self.linkMode():
                self.endLink()
            else:
                self.clearSelection()
        elif not event.modifiers() and len(self.selectedItems()) == 1:
            item = self.selectedItems()[0]
            if isinstance(item, EventItem):
                self.editEvent.emit(item)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            if event.button() & Qt.MouseButton.RightButton:
                self.endLink()
            # else:
            #     print('add new from scene')
            #     self.addNewNode.emit(self._placeholder)
        super().mouseReleaseEvent(event)


class EventsMindMapView(BaseGraphicsView):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene = EventsMindMapScene(self._novel)
        self.setScene(self._scene)
        # self.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))
        self.setBackgroundBrush(QColor('#e9ecef'))

        # self.scale(0.6, 0.6)

        self._scene.addNewNode.connect(self._displayNewNodeMenu)
        self._scene.editEvent.connect(self._editEvent)

    def _displayNewNodeMenu(self, placeholder: PlaceholderItem):
        menu = MenuWidget(self)
        menu.addAction(
            action('Event',
                   slot=lambda: self._scene.addNewItem(placeholder.sceneBoundingRect().center(), ItemType.Event)))

        view_pos = self.mapFromScene(placeholder.sceneBoundingRect().center())
        menu.exec(self.mapToGlobal(view_pos))

    def _editEvent(self, item: EventItem):
        def setText(text: str):
            item.setText(text)

        popup = TextLineEditorPopup(item.text(), item.textRect(), parent=self)
        view_pos = self.mapFromScene(item.textSceneRect().topLeft())
        popup.exec(self.mapToGlobal(view_pos))

        popup.aboutToHide.connect(lambda: setText(popup.text()))
