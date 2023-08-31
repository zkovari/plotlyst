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
from abc import abstractmethod
from enum import Enum
from functools import partial
from typing import Any, Optional, List

from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent, QPen, QPainterPath, QColor, QIcon, QResizeEvent, QTransform
from PyQt6.QtWidgets import QGraphicsView, QAbstractGraphicsShapeItem, QGraphicsItem, QGraphicsPathItem, QFrame, \
    QToolButton, QApplication, QGraphicsScene, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget
from overrides import overrides
from qthandy import hbox, margins, sp, incr_icon, vbox

from src.main.python.plotlyst.core.domain import Node
from src.main.python.plotlyst.view.common import shadow, tool_btn, frame, ExclusiveOptionalButtonGroup, \
    TooltipPositionEventFilter
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


class AbstractSocketItem(QAbstractGraphicsShapeItem):
    def __init__(self, orientation: Qt.Edge, parent=None):
        super().__init__(parent)
        self._size = 16
        self.setAcceptHoverEvents(True)
        self._orientation = orientation

        self._connectors: List[ConnectorItem] = []

    @overrides
    def boundingRect(self):
        return QRectF(0, 0, self._size, self._size)

    def addConnector(self, connector: 'ConnectorItem'):
        self._connectors.append(connector)

    def rearrangeConnectors(self):
        for con in self._connectors:
            con.rearrange()

    def removeConnectors(self):
        for con in self._connectors:
            self.scene().removeItem(con)
        self._connectors.clear()


class PlaceholderSocketItem(AbstractSocketItem):
    def __init__(self, parent=None):
        super().__init__(Qt.Edge.RightEdge, parent)
        self.setEnabled(False)
        self.setAcceptHoverEvents(False)

    @overrides
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        pass


class ConnectorItem(QGraphicsPathItem):

    def __init__(self, source: QAbstractGraphicsShapeItem, target: QAbstractGraphicsShapeItem,
                 pen: Optional[QPen] = None):
        super(ConnectorItem, self).__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self._source = source
        self._target = target
        if pen:
            self.setPen(pen)
        else:
            self.setPen(QPen(QColor(Qt.GlobalColor.darkBlue), 2))

        self.rearrange()

    def rearrange(self):
        self.setPos(self._source.sceneBoundingRect().center())

        path = QPainterPath()
        width = self._target.scenePos().x() - self.scenePos().x()
        height = self._target.scenePos().y() - self._source.scenePos().y()

        if abs(height) < 5:
            path.lineTo(width, height)
        else:
            path.quadTo(0, height / 2, width, height)

        self.setPath(path)

    def source(self) -> QAbstractGraphicsShapeItem:
        return self._source

    def target(self) -> QAbstractGraphicsShapeItem:
        return self._target


class NodeItem(QAbstractGraphicsShapeItem):
    def __init__(self, node: Node, parent=None):
        super().__init__(parent)
        self._node = node

        self.setPos(node.x, node.y)

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._posChangedTimer = QTimer()
        self._posChangedTimer.setInterval(1000)
        self._posChangedTimer.timeout.connect(self._posChangedOnTimeout)

    @overrides
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._posChangedTimer.start(1000)
            self._onPosChanged()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._onSelection(value)
        return super(NodeItem, self).itemChange(change, value)

    def _onPosChanged(self):
        pass

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
        connector = ConnectorItem(self._connectorPlaceholder.source(), target)
        self._connectorPlaceholder.source().addConnector(connector)
        target.addConnector(connector)
        self.addItem(connector)
        self.endLink()

    @overrides
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if (not self.isAdditionMode() and not self.linkMode() and
                event.button() & Qt.MouseButton.LeftButton and not self.itemAt(event.scenePos(), QTransform())):
            pass
            # self._selectionRect.start(event.scenePos())
            # self._selectionMode = True
        elif event.button() & Qt.MouseButton.RightButton or event.button() & Qt.MouseButton.MiddleButton:
            # disallow view movement to clear item selection
            return
        super().mousePressEvent(event)

    @overrides
    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.linkMode():
            if event.button() & Qt.MouseButton.RightButton:
                self.endLink()
        elif self.isAdditionMode() and event.button() & Qt.MouseButton.RightButton:
            self.cancelItemAddition.emit()
        # elif self._selectionMode and event.button() & Qt.MouseButton.LeftButton:
        #     self._selectionMode = False
        #     self._selectionRect.setVisible(False)
        #     self._updateSelection()
        elif self._additionMode is not None:
            self._addNewItem(self._additionMode, event.scenePos())

        super().mouseReleaseEvent(event)

    @abstractmethod
    def _addNewItem(self, itemType: NetworkItemType, scenePos: QPointF):
        pass


class NetworkGraphicsView(BaseGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor('#e9ecef'))
        self._scene = self._initScene()
        self.setScene(self._scene)

        self._wdgZoomBar = ZoomBar(self)
        self._wdgZoomBar.zoomed.connect(lambda x: self.scale(1.0 + x, 1.0 + x))

        self._controlsNavBar = self.__roundedFrame()
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

    def _endAddition(self, itemType: Optional[NetworkItemType] = None, item: Optional[NodeItem] = None):
        for btn in self._btnGroup.buttons():
            btn.setEnabled(True)
            if btn.isChecked():
                btn.setChecked(False)
        QApplication.restoreOverrideCursor()

    def __roundedFrame(self) -> QFrame:
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
