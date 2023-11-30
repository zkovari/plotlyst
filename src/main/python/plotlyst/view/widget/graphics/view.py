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

from functools import partial
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent, QColor, QIcon, QResizeEvent, QNativeGestureEvent
from PyQt6.QtWidgets import QGraphicsView, QGraphicsItem, QFrame, \
    QToolButton, QApplication, QWidget
from overrides import overrides
from qthandy import sp, incr_icon, vbox

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Diagram, DiagramNodeType, Character
from src.main.python.plotlyst.view.common import shadow, tool_btn, frame, ExclusiveOptionalButtonGroup, \
    TooltipPositionEventFilter
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorMenu
from src.main.python.plotlyst.view.widget.graphics import CharacterItem, ConnectorItem
from src.main.python.plotlyst.view.widget.graphics.editor import ZoomBar, ConnectorToolbar
from src.main.python.plotlyst.view.widget.graphics.items import NodeItem, EventItem
from src.main.python.plotlyst.view.widget.graphics.scene import NetworkScene


class BaseGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(BaseGraphicsView, self).__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self._moveOriginX = 0
        self._moveOriginY = 0
        self._scaledFactor: float = 1.0
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

    @overrides
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._moveOriginX = event.pos().x()
            self._moveOriginY = event.pos().y()
        else:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
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
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.dragMode() != QGraphicsView.DragMode.RubberBandDrag:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        super().mouseReleaseEvent(event)

    @overrides
    def event(self, event):
        if isinstance(event, QNativeGestureEvent):
            pinch: QNativeGestureEvent = event
            if pinch.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                scaleFactor = pinch.value()
                self._scale(scaleFactor)
            return True
        return super().event(event)

    @overrides
    def wheelEvent(self, event: QWheelEvent) -> None:
        super(BaseGraphicsView, self).wheelEvent(event)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            diff = event.angleDelta().y()
            scale = diff / 1200
            self._scale(round(scale, 1))

    def scaledFactor(self) -> float:
        return self._scaledFactor

    def _scale(self, scale: float):
        self._scaledFactor += scale
        self.scale(1.0 + scale, 1.0 + scale)


class NetworkGraphicsView(BaseGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setBackgroundBrush(QColor('#e9ecef'))
        self.setBackgroundBrush(QColor('#F2F2F2'))
        # self.setBackgroundBrush(QColor(RELAXED_WHITE_COLOR))
        self._diagram: Optional[Diagram] = None
        self._scene = self._initScene()
        self.setScene(self._scene)

        self._wdgZoomBar = ZoomBar(self)
        self._wdgZoomBar.zoomed.connect(self._scale)

        self._controlsNavBar = self._roundedFrame()
        sp(self._controlsNavBar).h_max()
        shadow(self._controlsNavBar)
        vbox(self._controlsNavBar, 5, 6)

        self._connectorEditor: Optional[ConnectorToolbar] = None

        self._btnGroup = ExclusiveOptionalButtonGroup()

        self._scene.itemAdded.connect(self._endAddition)
        self._scene.cancelItemAddition.connect(self._endAddition)
        self._scene.selectionChanged.connect(self._selectionChanged)
        self._scene.editItem.connect(self._editItem)
        self._scene.itemMoved.connect(self._itemMoved)
        self._scene.hideItemEditor.connect(self._hideItemToolbar)

    def setDiagram(self, diagram: Diagram):
        self._diagram = diagram
        self._scene.setDiagram(diagram)
        self.centerOn(0, 0)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._arrangeSideBars()

    @overrides
    def _scale(self, scale: float):
        super()._scale(scale)
        self._wdgZoomBar.updateScaledFactor(self.scaledFactor())

    def _mainControlClicked(self, itemType: DiagramNodeType, checked: bool):
        if checked:
            self._startAddition(itemType)
        else:
            self._endAddition()
            self._scene.endAdditionMode()

    def _newControlButton(self, icon: QIcon, tooltip: str, itemType: DiagramNodeType) -> QToolButton:
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

    def _startAddition(self, itemType: DiagramNodeType, subType: str = ''):
        for btn in self._btnGroup.buttons():
            if not btn.isChecked():
                btn.setDisabled(True)

        if not QApplication.overrideCursor():
            QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

        self._scene.startAdditionMode(itemType, subType)
        self.setToolTip(f'Click to add a new {itemType.name.lower()}')
        self._hideItemToolbar()

    def _endAddition(self, itemType: Optional[DiagramNodeType] = None, item: Optional[NodeItem] = None):
        for btn in self._btnGroup.buttons():
            btn.setEnabled(True)
            if btn.isChecked():
                btn.setChecked(False)
        QApplication.restoreOverrideCursor()
        self.setToolTip('')

        if item is not None and isinstance(item, CharacterItem):
            QTimer.singleShot(100, lambda: self._editCharacterItem(item))

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

    def _selectionChanged(self):
        if len(self._scene.selectedItems()) == 1:
            self._hideItemToolbar()
            self._showItemToolbar(self._scene.selectedItems()[0])
        else:
            self._hideItemToolbar()

    def _itemMoved(self, item: NodeItem):
        if len(self._scene.selectedItems()) == 1:
            self._showItemToolbar(item)

    def _editItem(self, item: NodeItem):
        if isinstance(item, CharacterItem):
            self._editCharacterItem(item)
        elif isinstance(item, EventItem):
            self._editEventItem(item)

    def _showItemToolbar(self, item: NodeItem):
        if isinstance(item, ConnectorItem):
            self._showConnectorToolbar(item)
        elif isinstance(item, CharacterItem):
            self._showCharacterItemToolbar(item)
        elif isinstance(item, EventItem):
            self._showEventItemToolbar(item)

    def _editCharacterItem(self, item: CharacterItem):
        def select(character: Character):
            item.setCharacter(character)

        popup = self._characterSelectorMenu()
        popup.selected.connect(select)
        view_pos = self.mapFromScene(item.sceneBoundingRect().topRight())
        popup.exec(self.mapToGlobal(view_pos))

    def _editEventItem(self, item: EventItem):
        pass

    def _showConnectorToolbar(self, item: ConnectorItem):
        if self._connectorEditor:
            self._connectorEditor.setItem(item)
            self._popupAbove(self._connectorEditor, item)

    def _showCharacterItemToolbar(self, item: CharacterItem):
        pass

    def _showEventItemToolbar(self, item: EventItem):
        pass

    def _hideItemToolbar(self):
        if self._connectorEditor:
            self._connectorEditor.setVisible(False)

    def _characterSelectorMenu(self) -> CharacterSelectorMenu:
        pass
