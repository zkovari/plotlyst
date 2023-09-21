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

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent, QColor, QIcon, QResizeEvent
from PyQt6.QtWidgets import QGraphicsView, QGraphicsItem, QFrame, \
    QToolButton, QApplication, QWidget
from overrides import overrides
from qthandy import sp, incr_icon, vbox

from src.main.python.plotlyst.core.domain import Diagram, DiagramNodeType
from src.main.python.plotlyst.view.common import shadow, tool_btn, frame, ExclusiveOptionalButtonGroup, \
    TooltipPositionEventFilter
from src.main.python.plotlyst.view.widget.graphics.editor import ZoomBar
from src.main.python.plotlyst.view.widget.graphics.items import NodeItem
from src.main.python.plotlyst.view.widget.graphics.scene import NetworkScene


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


class NetworkGraphicsView(BaseGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor('#e9ecef'))
        self._diagram: Optional[Diagram] = None
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

    def setDiagram(self, diagram: Diagram):
        self._diagram = diagram
        self._scene.setDiagram(diagram)
        self.centerOn(0, 0)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._arrangeSideBars()

    def _mainControlClicked(self, itemType: DiagramNodeType, checked: bool):
        if checked:
            self._startAddition(itemType)
        else:
            self._endAddition()

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

    def _endAddition(self, itemType: Optional[DiagramNodeType] = None, item: Optional[NodeItem] = None):
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
