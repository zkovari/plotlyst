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
from PyQt6.QtGui import QColor, QPainter, QPen, QKeyEvent, QFontMetrics, QResizeEvent, QTransform, QIcon
from PyQt6.QtWidgets import QGraphicsScene, QWidget, QAbstractGraphicsShapeItem, QGraphicsSceneHoverEvent, \
    QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QApplication, QGraphicsRectItem, QFrame, \
    QButtonGroup, QToolButton, QLabel, QGraphicsItem
from overrides import overrides
from qthandy import transparent, hbox, vbox, sp, margins, incr_icon, grid
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Novel, Character, CharacterNode, Node
from src.main.python.plotlyst.view.common import tool_btn, shadow, frame, ExclusiveOptionalButtonGroup, \
    TooltipPositionEventFilter
from src.main.python.plotlyst.view.icons import avatars, IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorMenu
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView, NodeItem, ConnectorItem, AbstractSocketItem
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


def v_center(ref_height: int, item_height: int) -> int:
    return (ref_height - item_height) // 2


class ItemType(Enum):
    EVENT = 1
    CHARACTER = 2
    GOAL = 3
    CONFLICT = 4
    DISTURBANCE = 5
    BACKSTORY = 6
    SETUP = 7
    QUESTION = 8
    FORESHADOWING = 9
    COMMENT = 10
    TOOL = 11
    COST = 12


class MindMapNode(NodeItem):
    def mindMapScene(self) -> 'EventsMindMapScene':
        return self.scene()

    def linkMode(self) -> bool:
        return self.mindMapScene().linkMode()


class SocketItem(AbstractSocketItem):
    def __init__(self, orientation: Qt.Edge, parent: 'ConnectableNode'):
        super().__init__(orientation, parent)

        self._size = 16
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self._linkAvailable = True
        self.setToolTip('Connect')

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

    def mindMapScene(self) -> 'EventsMindMapScene':
        return self.scene()


class SelectorRectItem(QGraphicsRectItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._startingPoint: QPointF = QPointF(0, 0)
        self._rect = QRectF()

        self.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DashLine))

    def start(self, pos: QPointF):
        self._startingPoint = pos
        self._rect.setTopLeft(pos)
        self.setRect(self._rect)

    def adjust(self, pos: QPointF):
        x1 = min(self._startingPoint.x(), pos.x())
        y1 = min(self._startingPoint.y(), pos.y())
        x2 = max(self._startingPoint.x(), pos.x())
        y2 = max(self._startingPoint.y(), pos.y())

        self._rect.setTopLeft(QPointF(x1, y1))
        self._rect.setBottomRight(QPointF(x2, y2))

        self.setRect(self._rect)


class PlaceholderItem(SocketItem):
    def __init__(self, parent=None):
        super().__init__(Qt.Edge.RightEdge, parent)
        self.setEnabled(False)
        self.setAcceptHoverEvents(False)
        self.setToolTip('Click to add a new node')


class StickerItem(MindMapNode):
    def __init__(self, node: Node, type: ItemType, parent=None):
        super().__init__(node, parent)
        self._size = 28
        self._icon = IconRegistry.from_name('mdi.comment-text', PLOTLYST_SECONDARY_COLOR)

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(RELAXED_WHITE_COLOR))
        painter.drawRect(3, 3, self._size - 6, self._size - 10)
        self._icon.paint(painter, 0, 0, self._size, self._size)

    @overrides
    def mouseDoubleClickEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        print('dclick')


class ConnectableNode(MindMapNode):
    def __init__(self, node: Node, parent=None):
        super().__init__(node, parent)
        self._sockets: List[SocketItem] = []

    def removeConnectors(self):
        for socket in self._sockets:
            socket.removeConnectors()

    @overrides
    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if self.linkMode() or event.modifiers() & Qt.KeyboardModifier.AltModifier:
            self._setSocketsVisible()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        if not self.isSelected():
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
    Margin: int = 30
    Padding: int = 20

    def __init__(self, node: Node, itemType: ItemType, parent=None):
        super().__init__(node, parent)
        self._text: str = 'New event'
        self._itemType = itemType
        self._icon: Optional[QIcon] = None
        self._iconSize: int = 0
        self._iconTextSpacing: int = 3
        if itemType == ItemType.GOAL:
            self._icon = IconRegistry.goal_icon()
        elif itemType == ItemType.CONFLICT:
            self._icon = IconRegistry.conflict_icon()
        elif itemType == ItemType.BACKSTORY:
            self._icon = IconRegistry.backstory_icon()
        elif itemType == ItemType.DISTURBANCE:
            self._icon = IconRegistry.inciting_incident_icon()
        elif itemType == ItemType.QUESTION:
            self._icon = IconRegistry.from_name('ei.question-sign')
        elif itemType == ItemType.SETUP:
            self._icon = IconRegistry.from_name('ri.seedling-fill')
        elif itemType == ItemType.FORESHADOWING:
            self._icon = IconRegistry.from_name('mdi6.crystal-ball')

        self._font = QApplication.font()
        # self._font.setPointSize(16)
        self._metrics = QFontMetrics(self._font)
        self._textRect: QRect = QRect(0, 0, 1, 1)
        self._width = 1
        self._height = 1
        self._nestedRectWidth = 1
        self._nestedRectHeight = 1

        self._socketLeft = SocketItem(Qt.Edge.LeftEdge, self)
        self._socketTopLeft = SocketItem(Qt.Edge.TopEdge, self)
        self._socketTopCenter = SocketItem(Qt.Edge.TopEdge, self)
        self._socketTopRight = SocketItem(Qt.Edge.TopEdge, self)
        self._socketRight = SocketItem(Qt.Edge.RightEdge, self)
        self._socketBottomLeft = SocketItem(Qt.Edge.BottomEdge, self)
        self._socketBottomCenter = SocketItem(Qt.Edge.BottomEdge, self)
        self._socketBottomRight = SocketItem(Qt.Edge.BottomEdge, self)
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
            painter.drawRoundedRect(self.Margin, self.Margin, self._nestedRectWidth, self._nestedRectHeight, 2, 2)

        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setFont(self._font)
        painter.drawText(self._textRect, Qt.AlignmentFlag.AlignCenter, self._text)
        painter.drawRoundedRect(self.Margin, self.Margin, self._nestedRectWidth, self._nestedRectHeight, 24, 24)

        if self._icon:
            self._icon.paint(painter, self.Margin + self.Padding - self._iconTextSpacing,
                             self.Margin + v_center(self.Padding * 2 + self._textRect.height(), self._iconSize),
                             self._iconSize, self._iconSize)

    @overrides
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.mindMapScene().editEventText(self)

    def _recalculateRect(self):
        self._textRect = self._metrics.boundingRect(self._text)
        self._iconSize = int(self._textRect.height() * 1.25) if self._icon else 0
        self._textRect.moveTopLeft(QPoint(self.Margin + self.Padding, self.Margin + self.Padding))
        self._textRect.moveTopLeft(QPoint(self._textRect.x() + self._iconSize, self._textRect.y()))

        self._width = self._textRect.width() + self._iconSize + self.Margin * 2 + self.Padding * 2
        self._height = self._textRect.height() + self.Margin * 2 + self.Padding * 2

        self._nestedRectWidth = self._textRect.width() + self.Padding * 2 + self._iconSize
        self._nestedRectHeight = self._textRect.height() + self.Padding * 2

        socketWidth = self._socketLeft.boundingRect().width()
        socketRad = socketWidth / 2
        socketPadding = (self.Margin - socketWidth) / 2
        self._socketTopCenter.setPos(self._width / 2 - socketRad, socketPadding)
        self._socketTopLeft.setPos(self._nestedRectWidth / 3 - socketRad, socketPadding)
        self._socketTopRight.setPos(self._nestedRectWidth, socketPadding)
        self._socketRight.setPos(self._width - self.Margin + socketPadding, self._height / 2 - socketRad)
        self._socketBottomCenter.setPos(self._width / 2 - socketRad, self._height - self.Margin + socketPadding)
        self._socketBottomLeft.setPos(self._nestedRectWidth / 3 - socketRad,
                                      self._height - self.Margin + socketPadding)
        self._socketBottomRight.setPos(self._nestedRectWidth, self._height - self.Margin + socketPadding)
        self._socketLeft.setPos(socketPadding, self._height / 2 - socketRad)


class CharacterItem(ConnectableNode):
    Margin: int = 25

    def __init__(self, node: Node, character: Optional[Character], parent=None):
        super().__init__(node, parent)
        self._character: Optional[Character] = character
        self._size: int = 68

        self._socketTop = SocketItem(Qt.Edge.TopEdge, self)
        self._socketRight = SocketItem(Qt.Edge.RightEdge, self)
        self._socketBottom = SocketItem(Qt.Edge.BottomEdge, self)
        self._socketLeft = SocketItem(Qt.Edge.LeftEdge, self)
        self._sockets.extend([self._socketLeft, self._socketTop, self._socketRight, self._socketBottom])
        socketSize = self._socketTop.boundingRect().width()
        half = self.Margin + v_center(self._size, socketSize)
        padding = v_center(self.Margin, socketSize)
        self._socketTop.setPos(half, padding)
        self._socketRight.setPos(self._size + self.Margin + padding, half)
        self._socketBottom.setPos(half, self._size + self.Margin + padding)
        self._socketLeft.setPos(padding, half)

        self._setSocketsVisible(False)

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size + self.Margin * 2, self._size + self.Margin * 2)

    def setCharacter(self, character: Character):
        self._character = character
        self.update()

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self.Margin, self.Margin, self._size, self._size, 2, 2)

        if self._character is None:
            avatar = IconRegistry.character_icon()
        else:
            avatar = avatars.avatar(self._character)
        avatar.paint(painter, self.Margin, self.Margin, self._size, self._size)


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


class SecondarySelectorWidget(QFrame):
    selected = pyqtSignal(ItemType)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty('relaxed-white-bg', True)
        self.setProperty('rounded', True)
        shadow(self)
        self._grid = grid(self)

        self._btnGroup = QButtonGroup()

    def _newButton(self, itemType: ItemType, icon: QIcon, tooltip: str, row: int, col: int) -> QToolButton:
        def clicked(toggled: bool):
            if toggled:
                self.selected.emit(itemType)

        btn = tool_btn(icon, tooltip,
                       True, icon_resize=False,
                       properties=['transparent-rounded-bg-on-hover', 'top-selector'],
                       parent=self)

        self._btnGroup.addButton(btn)
        self._grid.layout().addWidget(btn, row, col)
        btn.clicked.connect(clicked)

        return btn


class EventSelectorWidget(SecondarySelectorWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid.addWidget(QLabel('Events'), 0, 0, 1, 3)

        self._btnGeneral = self._newButton(ItemType.EVENT, IconRegistry.from_name('mdi.square-rounded-outline'),
                                           'Add new event', 1, 0)
        self._btnGoal = self._newButton(ItemType.GOAL, IconRegistry.goal_icon('black', 'black'), 'Add new goal', 1, 1)
        self._btnConflict = self._newButton(ItemType.CONFLICT, IconRegistry.conflict_icon('black', 'black'),
                                            'Add new Conflict', 1, 2)
        self._btnDisturbance = self._newButton(ItemType.DISTURBANCE, IconRegistry.inciting_incident_icon('black'),
                                               'Add new disturbance', 2,
                                               0)
        self._btnBackstory = self._newButton(ItemType.BACKSTORY, IconRegistry.backstory_icon('black', 'black'),
                                             'Add new backstory', 2, 1)

        self._grid.addWidget(QLabel('Narrative'), 3, 0, 1, 3)
        self._btnQuestion = self._newButton(ItemType.QUESTION, IconRegistry.from_name('ei.question-sign'),
                                            "Add new reader's question", 4,
                                            0)
        self._btnSetup = self._newButton(ItemType.SETUP, IconRegistry.from_name('ri.seedling-fill'),
                                         'Add new setup and payoff', 4, 1)
        self._btnForeshadowing = self._newButton(ItemType.FORESHADOWING, IconRegistry.from_name('mdi6.crystal-ball'),
                                                 'Add new foreshadowing',
                                                 4,
                                                 2)

        self._btnGeneral.setChecked(True)


class StickerSelectorWidget(SecondarySelectorWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._btnComment = self._newButton(ItemType.COMMENT, IconRegistry.from_name('mdi.comment-text-outline'),
                                           'Add new comment', 0, 0)
        self._btnTool = self._newButton(ItemType.TOOL, IconRegistry.tool_icon('black', 'black'), 'Add new tool', 0, 1)
        self._btnCost = self._newButton(ItemType.COST, IconRegistry.cost_icon('black', 'black'), 'Add new cost', 1, 0)

        self._btnComment.setChecked(True)


class EventsMindMapScene(QGraphicsScene):
    cancelItemAddition = pyqtSignal()
    itemAdded = pyqtSignal(ItemType, MindMapNode)
    editEvent = pyqtSignal(EventItem)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._linkMode: bool = False
        self._additionMode: Optional[ItemType] = None

        self._selectionMode = False
        self._selectionRect = SelectorRectItem()
        self.addItem(self._selectionRect)
        self._selectionRect.setVisible(False)

        self._placeholder: Optional[PlaceholderItem] = None
        self._connectorPlaceholder: Optional[ConnectorItem] = None

        if novel.characters:
            characterItem = CharacterItem(CharacterNode(50, 50), novel.characters[0])

            self.addItem(characterItem)
        eventItem = EventItem(Node(400, 100), ItemType.EVENT)
        self.addItem(eventItem)

        sticker = StickerItem(Node(200, 0), ItemType.COMMENT)
        self.addItem(sticker)

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

    def isAdditionMode(self) -> bool:
        return self._additionMode is not None

    def startAdditionMode(self, mode: ItemType):
        self._additionMode = mode

    def endAdditionMode(self):
        self._additionMode = None

    @overrides
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            if self.linkMode():
                self.endLink()
            elif self.isAdditionMode():
                self.cancelItemAddition.emit()
            else:
                self.clearSelection()
        elif event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            for item in self.selectedItems():
                if isinstance(item, ConnectableNode):
                    item.removeConnectors()
                self.removeItem(item)
        elif not event.modifiers() and len(self.selectedItems()) == 1:
            item = self.selectedItems()[0]
            if isinstance(item, EventItem):
                self.editEvent.emit(item)

    @overrides
    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if (not self.isAdditionMode() and not self.linkMode() and
                event.button() & Qt.MouseButton.LeftButton and not self.itemAt(event.scenePos(), QTransform())):
            self._selectionRect.start(event.scenePos())
            self._selectionMode = True
        elif event.button() & Qt.MouseButton.RightButton or event.button() & Qt.MouseButton.MiddleButton:
            # disallow view movement to clear item selection
            return
        super().mousePressEvent(event)

    @overrides
    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            self._placeholder.setPos(event.scenePos())
            self._connectorPlaceholder.rearrange()
        elif self._selectionMode:
            self._selectionRect.adjust(event.scenePos())
            self._selectionRect.setVisible(True)
            self._updateSelection()
        super().mouseMoveEvent(event)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            if event.button() & Qt.MouseButton.RightButton:
                self.endLink()
        elif self.isAdditionMode() and event.button() & Qt.MouseButton.RightButton:
            self.cancelItemAddition.emit()
        elif self._selectionMode and event.button() & Qt.MouseButton.LeftButton:
            self._selectionMode = False
            self._selectionRect.setVisible(False)
            self._updateSelection()
        elif self._additionMode is not None:
            self._addNewEvent(self._additionMode, event.scenePos())

        super().mouseReleaseEvent(event)

    def _addNewEvent(self, itemType: ItemType, scenePos: QPointF):
        if itemType == ItemType.CHARACTER:
            item = CharacterItem(self.toCharacterNode(scenePos), character=None)
        elif itemType == ItemType.COMMENT:
            item = StickerItem(Node(scenePos.x(), scenePos.y()), itemType)
        else:
            item = EventItem(self.toEventNode(scenePos), itemType)

        self.addItem(item)
        self.itemAdded.emit(itemType, item)

    def _updateSelection(self):
        if not self._selectionRect.rect().isValid():
            return
        self.clearSelection()
        items_in_rect = self.items(self._selectionRect.rect(), Qt.ItemSelectionMode.IntersectsItemBoundingRect)
        for item in items_in_rect:
            item.setSelected(True)

    @staticmethod
    def toEventNode(scenePos: QPointF) -> Node:
        node = Node(scenePos.x(), scenePos.y())
        node.x = node.x - EventItem.Margin - EventItem.Padding
        node.y = node.y - EventItem.Margin - EventItem.Padding
        return node

    @staticmethod
    def toCharacterNode(scenePos: QPointF) -> Node:
        node = Node(scenePos.x(), scenePos.y())
        node.x = node.x - CharacterItem.Margin
        node.y = node.y - CharacterItem.Margin
        return node


class EventsMindMapView(BaseGraphicsView):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene = EventsMindMapScene(self._novel)
        self.setScene(self._scene)
        self.setBackgroundBrush(QColor('#e9ecef'))

        self._scene.itemAdded.connect(self._endAddition)
        self._scene.cancelItemAddition.connect(self._endAddition)
        self._scene.editEvent.connect(self._editEvent)

        self._controlsNavBar = self.__roundedFrame(self)
        sp(self._controlsNavBar).h_max()
        shadow(self._controlsNavBar)

        self._btnAddEvent = tool_btn(
            IconRegistry.from_name('mdi6.shape-square-rounded-plus'), 'Add new event', True,
            icon_resize=False, properties=['transparent-rounded-bg-on-hover', 'top-selector'],
            parent=self._controlsNavBar)
        self._btnAddCharacter = tool_btn(
            IconRegistry.character_icon('#040406'), 'Add new character', True,
            icon_resize=False, properties=['transparent-rounded-bg-on-hover', 'top-selector'],
            parent=self._controlsNavBar)
        self._btnAddSticker = tool_btn(IconRegistry.from_name('mdi6.sticker-circle-outline'), 'Add new sticker',
                                       True, icon_resize=False,
                                       properties=['transparent-rounded-bg-on-hover', 'top-selector'],
                                       parent=self._controlsNavBar)
        self._btnGroup = ExclusiveOptionalButtonGroup()
        self._btnGroup.addButton(self._btnAddEvent)
        self._btnGroup.addButton(self._btnAddCharacter)
        self._btnGroup.addButton(self._btnAddSticker)
        for btn in self._btnGroup.buttons():
            btn.installEventFilter(TooltipPositionEventFilter(btn))
            incr_icon(btn, 2)
        self._btnGroup.buttonClicked.connect(self._mainControlClicked)
        vbox(self._controlsNavBar, 5, 6)
        self._controlsNavBar.layout().addWidget(self._btnAddEvent)
        self._controlsNavBar.layout().addWidget(self._btnAddCharacter)
        self._controlsNavBar.layout().addWidget(self._btnAddSticker)

        self._wdgSecondaryEventSelector = EventSelectorWidget(self)
        self._wdgSecondaryEventSelector.setVisible(False)
        self._wdgSecondaryEventSelector.selected.connect(self._startAddition)
        self._wdgSecondaryStickerSelector = StickerSelectorWidget(self)
        self._wdgSecondaryStickerSelector.setVisible(False)
        self._wdgSecondaryStickerSelector.selected.connect(self._startAddition)

        self._wdgZoomBar = self.__roundedFrame(self)
        shadow(self._wdgZoomBar)
        hbox(self._wdgZoomBar, 2, spacing=6)
        margins(self._wdgZoomBar, left=10, right=10)

        self._btnZoomIn = tool_btn(IconRegistry.plus_circle_icon('lightgrey'), 'Zoom in', transparent_=True,
                                   parent=self._wdgZoomBar)
        self._btnZoomOut = tool_btn(IconRegistry.minus_icon('lightgrey'), 'Zoom out', transparent_=True,
                                    parent=self._wdgZoomBar)
        self._btnZoomIn.clicked.connect(lambda: self.scale(1.1, 1.1))
        self._btnZoomOut.clicked.connect(lambda: self.scale(0.9, 0.9))

        self._wdgZoomBar.layout().addWidget(self._btnZoomOut)
        self._wdgZoomBar.layout().addWidget(self._btnZoomIn)
        self.__arrangeSideBars()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super(EventsMindMapView, self).resizeEvent(event)
        self.__arrangeSideBars()

    def _editEvent(self, item: EventItem):
        def setText(text: str):
            item.setText(text)

        popup = TextLineEditorPopup(item.text(), item.textRect(), parent=self)
        view_pos = self.mapFromScene(item.textSceneRect().topLeft())
        popup.exec(self.mapToGlobal(view_pos))

        popup.aboutToHide.connect(lambda: setText(popup.text()))

    def _mainControlClicked(self):
        self._wdgSecondaryEventSelector.setHidden(True)
        self._wdgSecondaryStickerSelector.setHidden(True)

        if self._btnAddEvent.isChecked():
            self._wdgSecondaryEventSelector.setVisible(True)
            self._startAddition(ItemType.EVENT)
        elif self._btnAddCharacter.isChecked():
            self._startAddition(ItemType.CHARACTER)
        elif self._btnAddSticker.isChecked():
            self._wdgSecondaryStickerSelector.setVisible(True)
            self._startAddition(ItemType.COMMENT)
        else:
            self._endAddition()

    def _startAddition(self, itemType: ItemType):
        self._scene.startAdditionMode(itemType)

        if not QApplication.overrideCursor():
            QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def _endAddition(self, itemType: Optional[ItemType] = None, item: Optional[MindMapNode] = None):
        btn = self._btnGroup.checkedButton()
        if btn:
            btn.setChecked(False)
        QApplication.restoreOverrideCursor()
        self._wdgSecondaryEventSelector.setHidden(True)
        self._wdgSecondaryStickerSelector.setHidden(True)
        self._scene.endAdditionMode()

        if itemType == ItemType.CHARACTER:
            self._endCharacterAddition(item)

    def _endCharacterAddition(self, item: CharacterItem):
        def select(character: Character):
            item.setCharacter(character)

        popup = CharacterSelectorMenu(self._novel, parent=self)
        popup.selected.connect(select)
        view_pos = self.mapFromScene(item.sceneBoundingRect().topRight())
        popup.exec(self.mapToGlobal(view_pos))

    def __arrangeSideBars(self):
        self._wdgZoomBar.setGeometry(10, self.height() - self._wdgZoomBar.sizeHint().height() - 10,
                                     self._wdgZoomBar.sizeHint().width(),
                                     self._wdgZoomBar.sizeHint().height())
        self._controlsNavBar.setGeometry(10, 100, self._controlsNavBar.sizeHint().width(),
                                         self._controlsNavBar.sizeHint().height())

        secondary_x = self._controlsNavBar.pos().x() + self._controlsNavBar.sizeHint().width() + 5
        secondary_y = self._controlsNavBar.pos().y() + self._btnAddEvent.pos().y()
        self._wdgSecondaryEventSelector.setGeometry(secondary_x, secondary_y,
                                                    self._wdgSecondaryEventSelector.sizeHint().width(),
                                                    self._wdgSecondaryEventSelector.sizeHint().height())

        secondary_x = self._controlsNavBar.pos().x() + self._controlsNavBar.sizeHint().width() + 5
        secondary_y = self._controlsNavBar.pos().y() + self._btnAddSticker.pos().y()
        self._wdgSecondaryStickerSelector.setGeometry(secondary_x, secondary_y,
                                                      self._wdgSecondaryStickerSelector.sizeHint().width(),
                                                      self._wdgSecondaryStickerSelector.sizeHint().height())

    @staticmethod
    def __roundedFrame(parent=None) -> QFrame:
        frame_ = frame(parent)
        frame_.setProperty('relaxed-white-bg', True)
        frame_.setProperty('rounded', True)
        return frame_
