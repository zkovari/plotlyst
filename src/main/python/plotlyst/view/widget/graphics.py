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
import math
from abc import abstractmethod
from enum import Enum
from functools import partial
from typing import Any, Optional, List

from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent, QPen, QPainterPath, QColor, QIcon, QResizeEvent, QTransform, \
    QKeyEvent, QPolygonF, QPaintEvent
from PyQt6.QtWidgets import QGraphicsView, QAbstractGraphicsShapeItem, QGraphicsItem, QGraphicsPathItem, QFrame, \
    QToolButton, QApplication, QGraphicsScene, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget, \
    QGraphicsRectItem, QGraphicsSceneHoverEvent, QGraphicsPolygonItem, QAbstractButton, QSlider, QButtonGroup
from overrides import overrides
from qthandy import hbox, margins, sp, incr_icon, vbox, grid

from src.main.python.plotlyst.common import PLOTLYST_TERTIARY_COLOR, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Node, Relation
from src.main.python.plotlyst.view.common import shadow, tool_btn, frame, ExclusiveOptionalButtonGroup, \
    TooltipPositionEventFilter, pointy
from src.main.python.plotlyst.view.icons import IconRegistry


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


class IconBadge(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._size: int = 32
        self._icon: Optional[QIcon] = None
        self._color: str = 'black'

    def setIcon(self, icon: QIcon, borderColor: Optional[str] = None):
        self._icon = icon
        if borderColor:
            self._color = borderColor
        self.update()

    @overrides
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: Optional[QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QPen(QColor(self._color), 2))
        painter.setBrush(QColor(RELAXED_WHITE_COLOR))
        painter.drawEllipse(0, 0, self._size, self._size)

        if self._icon:
            self._icon.paint(painter, 3, 3, self._size - 5, self._size - 5)


class AbstractSocketItem(QAbstractGraphicsShapeItem):
    def __init__(self, angle: float, size: int = 16, parent=None):
        super().__init__(parent)
        self._size = size
        self._angle: float = angle
        self._hovered = False
        self._linkAvailable = True

        self.setToolTip('Connect')
        self.setAcceptHoverEvents(True)

        self._connectors: List[ConnectorItem] = []

    def angle(self) -> float:
        return self._angle

    def setAngle(self, angle: float):
        self._angle = angle

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, self._size, self._size)

    @overrides
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hovered = True
        if self.networkScene().linkMode() and self.networkScene().linkSource().parentItem() == self.parentItem():
            self._linkAvailable = False
        else:
            self._linkAvailable = True
        self.setToolTip('Connect' if self._linkAvailable else 'Cannot connect to itself')
        self.prepareGeometryChange()
        self.update()

    @overrides
    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self._hovered = False
        self._linkAvailable = True
        self.setToolTip('Connect')
        self.prepareGeometryChange()
        self.update()

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    @overrides
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.networkScene().linkMode():
            if self.networkScene().linkSource().parentItem() != self.parentItem():
                self.networkScene().link(self)
        else:
            self.networkScene().startLink(self)

    def addConnector(self, connector: 'ConnectorItem'):
        self._connectors.append(connector)

    def rearrangeConnectors(self):
        for con in self._connectors:
            con.rearrange()

    def removeConnectors(self):
        for con in self._connectors:
            self.scene().removeItem(con)
        self._connectors.clear()

    def networkScene(self) -> 'NetworkScene':
        return self.scene()


class PlaceholderSocketItem(AbstractSocketItem):
    def __init__(self, parent=None):
        super().__init__(0, parent=parent)
        self.setEnabled(False)
        self.setAcceptHoverEvents(False)

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        pass


class ConnectorItem(QGraphicsPathItem):

    def __init__(self, source: AbstractSocketItem, target: AbstractSocketItem,
                 pen: Optional[QPen] = None):
        super(ConnectorItem, self).__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self._source = source
        self._target = target
        self._color: str = 'darkblue'
        self._relation: Optional[Relation] = None
        self._icon: Optional[QIcon] = None
        if pen:
            self.setPen(pen)
        else:
            self.setPen(QPen(QColor(self._color), 2))

        self._arrowhead = QPolygonF([
            QPointF(0, -5),
            QPointF(10, 0),
            QPointF(0, 5),
        ])
        self._arrowheadItem = QGraphicsPolygonItem(self._arrowhead, self)
        self._arrowheadItem.setPen(QPen(QColor(Qt.GlobalColor.darkBlue), 1))
        self._arrowheadItem.setBrush(QColor(Qt.GlobalColor.darkBlue))

        self._iconBadge = IconBadge(self)
        self._iconBadge.setVisible(False)

        self.rearrange()

    def penStyle(self) -> Qt.PenStyle:
        return self.pen().style()

    def setPenStyle(self, penStyle: Qt.PenStyle):
        pen = self.pen()
        pen.setStyle(penStyle)
        self.setPen(pen)
        self.update()

    def penWidth(self) -> int:
        return self.pen().width()

    def setPenWidth(self, width: int):
        pen = self.pen()
        pen.setWidth(width)
        self.setPen(pen)

        arrowPen = self._arrowheadItem.pen()
        prevWidth = arrowPen.width()
        self._arrowheadItem.setScale(1.0 + (width - prevWidth) / 10)

        self.rearrange()

    def relation(self) -> Optional[Relation]:
        return self._relation

    def setRelation(self, relation: Relation):
        pen = self.pen()
        color = QColor(relation.icon_color)
        pen.setColor(color)
        self.setPen(pen)

        arrowPen = self._arrowheadItem.pen()
        arrowPen.setColor(color)
        arrowPen.setBrush(color)
        self._arrowheadItem.setPen(arrowPen)

        self._relation = relation
        self._icon = IconRegistry.from_name(relation.icon, relation.icon_color)
        self._color = relation.icon_color
        self._iconBadge.setIcon(self._icon, self._color)
        self._iconBadge.setVisible(True)

        self.rearrange()

    def icon(self) -> Optional[QIcon]:
        return self._icon

    def setIcon(self, icon: QIcon):
        self._icon = icon
        self._iconBadge.setIcon(self._icon, self._color)
        self._iconBadge.setVisible(True)
        self.rearrange()

    def rearrange(self):
        self.setPos(self._source.sceneBoundingRect().center())

        path = QPainterPath()

        start = self.scenePos()
        end = self._target.sceneBoundingRect().center()

        width = end.x() - start.x()
        height = end.y() - start.y()

        angle = math.degrees(math.atan2(-height / 2, width))
        if abs(height) < 5:
            line = True
            path.lineTo(width, height)
        else:
            line = False
            if self._source.angle() >= 0:
                path.quadTo(0, height / 2, width, height)
            else:
                path.quadTo(width / 2, -height / 2, width, height)
                angle = math.degrees(math.atan2(-height / 2, width / 2))

        self._arrowheadItem.setPos(width, height)
        self._arrowheadItem.setRotation(-angle)

        if self._icon:
            if line:
                point = path.pointAtPercent(0.4)
            else:
                point = path.pointAtPercent(0.6)
            self._iconBadge.setPos(point.x() - self._iconBadge.boundingRect().width() / 2,
                                   point.y() - self._iconBadge.boundingRect().height() / 2)

        # if line:
        #     point = path.pointAtPercent(0.4)
        # else:
        #     point = path.pointAtPercent(0.6)
        # path.addText(point, QApplication.font(), 'Romance')
        self.setPath(path)

    def source(self) -> QAbstractGraphicsShapeItem:
        return self._source

    def target(self) -> QAbstractGraphicsShapeItem:
        return self._target


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


class NodeItem(QAbstractGraphicsShapeItem):
    def __init__(self, node: Node, parent=None):
        super().__init__(parent)
        self._node = node

        self.setPos(node.x, node.y)
        self._sockets: List[AbstractSocketItem] = []

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._posChangedTimer = QTimer()
        self._posChangedTimer.setInterval(1000)
        self._posChangedTimer.timeout.connect(self._posChangedOnTimeout)

    def networkScene(self) -> 'NetworkScene':
        return self.scene()

    def removeConnectors(self):
        for socket in self._sockets:
            socket.removeConnectors()

    @overrides
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._posChangedTimer.start(1000)
            self._onPosChanged()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._onSelection(value)
        return super(NodeItem, self).itemChange(change, value)

    def _onPosChanged(self):
        for socket in self._sockets:
            socket.rearrangeConnectors()

    def _onSelection(self, selected: bool):
        pass

    def _posChangedOnTimeout(self):
        self._posChangedTimer.stop()
        self._node.x = self.scenePos().x()
        self._node.y = self.scenePos().y()


class BaseGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(BaseGraphicsView, self).__init__(parent)
        self._moveOriginX = 0
        self._moveOriginY = 0
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()
        super(BaseGraphicsView, self).mousePressEvent(event)

    @overrides
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.itemAt(
                event.pos()) and (
                event.buttons() & Qt.MouseButton.MiddleButton or event.buttons() & Qt.MouseButton.RightButton):
            oldPoint = self.mapToScene(self._moveOriginX, self._moveOriginY)
            newPoint = self.mapToScene(event.pos())
            translation = newPoint - oldPoint
            self.translate(translation.x(), translation.y())

            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()
        super(BaseGraphicsView, self).mouseMoveEvent(event)

    @overrides
    def wheelEvent(self, event: QWheelEvent) -> None:
        super(BaseGraphicsView, self).wheelEvent(event)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            diff = event.angleDelta().y()
            scale = diff / 1200
            self.scale(1 + scale, 1 + scale)


class NetworkItemType(Enum):
    pass


class NetworkScene(QGraphicsScene):
    cancelItemAddition = pyqtSignal()
    itemAdded = pyqtSignal(NetworkItemType, NodeItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._linkMode: bool = False
        self._additionMode: Optional[NetworkItemType] = None

        self._placeholder: Optional[PlaceholderSocketItem] = None
        self._connectorPlaceholder: Optional[ConnectorItem] = None

        self._selectionMode = False
        self._selectionRect = SelectorRectItem()
        self.addItem(self._selectionRect)
        self._selectionRect.setVisible(False)

    def isAdditionMode(self) -> bool:
        return self._additionMode is not None

    def startAdditionMode(self, itemType: NetworkItemType):
        self._additionMode = itemType

    def endAdditionMode(self):
        self._additionMode = None

    def linkMode(self) -> bool:
        return self._linkMode

    def linkSource(self) -> Optional[AbstractSocketItem]:
        if self._connectorPlaceholder is not None:
            return self._connectorPlaceholder.source()

    def startLink(self, source: AbstractSocketItem):
        self._linkMode = True
        self._placeholder = PlaceholderSocketItem()
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

    def link(self, target: AbstractSocketItem):
        self._onLink(self._connectorPlaceholder.source().parentItem(), self._connectorPlaceholder.source(),
                     target.parentItem(), target)
        connector = ConnectorItem(self._connectorPlaceholder.source(), target)
        self._connectorPlaceholder.source().addConnector(connector)
        target.addConnector(connector)
        self.addItem(connector)
        self.endLink()

    @overrides
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            if self.linkMode():
                self.endLink()
            elif self.isAdditionMode():
                self.cancelItemAddition.emit()
                self.endAdditionMode()
            else:
                self.clearSelection()
        elif event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            for item in self.selectedItems():
                if isinstance(item, NodeItem):
                    item.removeConnectors()
                self.removeItem(item)

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if (not self.isAdditionMode() and not self.linkMode() and
                event.button() & Qt.MouseButton.LeftButton and not self.itemAt(event.scenePos(), QTransform())):
            self._selectionRect.start(event.scenePos())
            # self._selectionMode = True
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
            self.endAdditionMode()
        elif self._selectionMode and event.button() & Qt.MouseButton.LeftButton:
            self._selectionMode = False
            self._selectionRect.setVisible(False)
            self._updateSelection()
        elif self._additionMode is not None:
            self._addNewItem(self._additionMode, event.scenePos())

        super().mouseReleaseEvent(event)

    @abstractmethod
    def _addNewItem(self, itemType: NetworkItemType, scenePos: QPointF):
        pass

    def _onLink(self, sourceNode: NodeItem, sourceSocket: AbstractSocketItem, targetNode: NodeItem,
                targetSocket: AbstractSocketItem):
        pass

    def _updateSelection(self):
        if not self._selectionRect.rect().isValid():
            return
        self.clearSelection()
        items_in_rect = self.items(self._selectionRect.rect(), Qt.ItemSelectionMode.IntersectsItemBoundingRect)
        for item in items_in_rect:
            item.setSelected(True)


class NetworkGraphicsView(BaseGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor('#e9ecef'))
        self._scene = self._initScene()
        self.setScene(self._scene)

        self._wdgZoomBar = ZoomBar(self)
        self._wdgZoomBar.zoomed.connect(lambda x: self.scale(1.0 + x, 1.0 + x))

        self._controlsNavBar = self._roundedFrame()
        sp(self._controlsNavBar).h_max()
        shadow(self._controlsNavBar)
        vbox(self._controlsNavBar, 5, 6)

        self._btnGroup = ExclusiveOptionalButtonGroup()

        self._scene.itemAdded.connect(self._endAddition)
        self._scene.cancelItemAddition.connect(self._endAddition)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._arrangeSideBars()

    def _mainControlClicked(self, itemType: NetworkItemType, checked: bool):
        if checked:
            self._startAddition(itemType)
        else:
            self._endAddition()

    def _newControlButton(self, icon: QIcon, tooltip: str, itemType: NetworkItemType) -> QToolButton:
        btn = tool_btn(icon, tooltip,
                       True, icon_resize=False,
                       properties=['transparent-rounded-bg-on-hover', 'top-selector'],
                       parent=self._controlsNavBar)

        btn.installEventFilter(TooltipPositionEventFilter(btn))
        incr_icon(btn, 2)

        self._btnGroup.addButton(btn)
        self._controlsNavBar.layout().addWidget(btn)
        btn.clicked.connect(partial(self._mainControlClicked, itemType))

        return btn

    def _startAddition(self, itemType: NetworkItemType):
        for btn in self._btnGroup.buttons():
            if not btn.isChecked():
                btn.setDisabled(True)

        if not QApplication.overrideCursor():
            QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

        self._scene.startAdditionMode(itemType)
        self.setToolTip(f'Click to add a new {itemType.name.lower()}')

    def _endAddition(self, itemType: Optional[NetworkItemType] = None, item: Optional[NodeItem] = None):
        for btn in self._btnGroup.buttons():
            btn.setEnabled(True)
            if btn.isChecked():
                btn.setChecked(False)
        QApplication.restoreOverrideCursor()
        self.setToolTip('')

    def _roundedFrame(self) -> QFrame:
        frame_ = frame(self)
        frame_.setProperty('relaxed-white-bg', True)
        frame_.setProperty('rounded', True)
        return frame_

    def _arrangeSideBars(self):
        self._wdgZoomBar.setGeometry(10, self.height() - self._wdgZoomBar.sizeHint().height() - 10,
                                     self._wdgZoomBar.sizeHint().width(),
                                     self._wdgZoomBar.sizeHint().height())
        self._controlsNavBar.setGeometry(10, 100, self._controlsNavBar.sizeHint().width(),
                                         self._controlsNavBar.sizeHint().height())

    def _popupAbove(self, widget: QWidget, refItem: QGraphicsItem):
        item_w = refItem.sceneBoundingRect().width()
        editor_w = widget.sizeHint().width()
        diff_w = int(editor_w - item_w) // 2

        view_pos = self.mapFromScene(refItem.sceneBoundingRect().topLeft())
        view_pos.setX(view_pos.x() - diff_w)
        view_pos.setY(view_pos.y() - 50)
        widget.move(view_pos)
        widget.setVisible(True)

    def _initScene(self):
        return NetworkScene()


class ZoomBar(QFrame):
    zoomed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setProperty('relaxed-white-bg', True)
        self.setProperty('rounded', True)

        shadow(self)
        hbox(self, 2, spacing=6)
        margins(self, left=10, right=10)

        self._btnZoomIn = tool_btn(IconRegistry.plus_circle_icon('lightgrey'), 'Zoom in', transparent_=True,
                                   parent=self)
        self._btnZoomOut = tool_btn(IconRegistry.minus_icon('lightgrey'), 'Zoom out', transparent_=True,
                                    parent=self)
        self._btnZoomIn.clicked.connect(lambda: self.zoomed.emit(0.1))
        self._btnZoomOut.clicked.connect(lambda: self.zoomed.emit(-0.1))

        self.layout().addWidget(self._btnZoomOut)
        self.layout().addWidget(self._btnZoomIn)


class SecondarySelectorWidget(QFrame):
    selected = pyqtSignal(NetworkItemType)

    def __init__(self, parent=None, optional: bool = False):
        super().__init__(parent)
        self.setProperty('relaxed-white-bg', True)
        self.setProperty('rounded', True)
        shadow(self)
        self._grid = grid(self, h_spacing=5, v_spacing=3)
        margins(self, left=5, right=5)

        if optional:
            self._btnGroup = ExclusiveOptionalButtonGroup()
        else:
            self._btnGroup = QButtonGroup()

    def _newButton(self, icon: QIcon, tooltip: str, row: int,
                   col: int) -> QToolButton:
        btn = tool_btn(icon, tooltip,
                       True, icon_resize=False,
                       properties=['transparent-rounded-bg-on-hover', 'top-selector'],
                       parent=self)
        self._btnGroup.addButton(btn)
        self._grid.layout().addWidget(btn, row, col)

        return btn

    def _newItemTypeButton(self, itemType: NetworkItemType, icon: QIcon, tooltip: str, row: int,
                           col: int) -> QToolButton:
        def clicked(toggled: bool):
            if toggled:
                self.selected.emit(itemType)

        btn = self._newButton(icon, tooltip, row, col)
        btn.clicked.connect(clicked)

        return btn


class BaseItemEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        vbox(self, spacing=5)
        self._toolbar = QFrame(self)
        self._toolbar.setProperty('relaxed-white-bg', True)
        self._toolbar.setProperty('rounded', True)
        shadow(self._toolbar)

        hbox(self._toolbar, 5, spacing=6)
        self.layout().addWidget(self._toolbar)

        self._secondaryWidgets = []

    def addSecondaryWidget(self, btn: QAbstractButton, widget: QWidget, alignment=Qt.AlignmentFlag.AlignLeft):
        self._secondaryWidgets.append(widget)
        sp(widget).h_max()
        self.layout().addWidget(widget, alignment)
        btn.clicked.connect(partial(self._toggleSecondarySelector, widget))
        widget.setVisible(False)

    def _toggleSecondarySelector(self, secondary: QWidget):
        secondary.setVisible(not secondary.isVisible())
        if secondary.isVisible():
            self.setFixedHeight(self._toolbar.sizeHint().height() + secondary.sizeHint().height())
        else:
            self.setFixedHeight(self._toolbar.sizeHint().height())

    def _hideSecondarySelectors(self):
        for wdg in self._secondaryWidgets:
            wdg.setVisible(False)
        self.setFixedHeight(self._toolbar.sizeHint().height())


class PenStyleSelector(QAbstractButton):
    penStyleToggled = pyqtSignal(Qt.PenStyle, bool)

    def __init__(self, penWidth: int = 2, color=Qt.GlobalColor.black, colorOn=PLOTLYST_TERTIARY_COLOR,
                 parent=None):
        super().__init__(parent)
        self._penWidth = penWidth
        self._color = color
        self._colorOn = colorOn
        self._penStyle = self.penStyle()
        self.setFixedSize(20, 20)

        self.setCheckable(True)

        self._pen = QPen(QColor(self._color), self._penWidth, self._penStyle)
        self._penToggled = QPen(QColor(self._colorOn), self._penWidth, self._penStyle)
        pointy(self)

    @abstractmethod
    def penStyle(self) -> Qt.PenStyle:
        pass

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isChecked():
            painter.setPen(self._penToggled)
        else:
            painter.setPen(self._pen)
        painter.drawLine(0, self.rect().height() // 2, self.rect().width(), self.rect().height() // 2)


class SolidPenStyleSelector(PenStyleSelector):

    @overrides
    def penStyle(self) -> Qt.PenStyle:
        return Qt.PenStyle.SolidLine


class DashPenStyleSelector(PenStyleSelector):

    @overrides
    def penStyle(self) -> Qt.PenStyle:
        return Qt.PenStyle.DashLine


class DotPenStyleSelector(PenStyleSelector):

    @overrides
    def penStyle(self) -> Qt.PenStyle:
        return Qt.PenStyle.DotLine


class PenWidthEditor(QSlider):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(1)
        self.setMaximum(10)
        self.setOrientation(Qt.Orientation.Horizontal)


class RelationsButton(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = IconRegistry.character_icon()
        self.setFixedSize(40, 20)
        pointy(self)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(Qt.GlobalColor.black, 1))

        x = 5
        y = 2
        painter.drawEllipse(x, y, self.rect().width() - x * 2, self.rect().height() - y * 2)

        self._icon.paint(painter, 0, y, 15, 15)
        self._icon.paint(painter, self.rect().width() - 15, y, 15, 15)
