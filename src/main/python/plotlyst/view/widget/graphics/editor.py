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
from functools import partial

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon, QPaintEvent, QKeySequence
from PyQt6.QtWidgets import QFrame, \
    QToolButton, QWidget, \
    QAbstractButton, QSlider, QButtonGroup, QPushButton
from overrides import overrides
from qthandy import hbox, margins, sp, vbox, grid, pointy

from src.main.python.plotlyst.common import PLOTLYST_TERTIARY_COLOR
from src.main.python.plotlyst.core.domain import DiagramNodeType
from src.main.python.plotlyst.view.common import shadow, tool_btn, ExclusiveOptionalButtonGroup
from src.main.python.plotlyst.view.icons import IconRegistry


class ZoomBar(QFrame):
    zoomed = pyqtSignal(float)
    reset = pyqtSignal()

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
        self._btnZoomIn.setShortcut(QKeySequence.StandardKey.ZoomIn)

        self._btnScaledFactor = QPushButton()
        self._btnScaledFactor.setStyleSheet('border: 0px; color: lightgrey;')
        # pointy(self._btnScaledFactor)
        # self._btnScaledFactor.installEventFilter(ButtonPressResizeEventFilter(self._btnScaledFactor))
        # self._btnScaledFactor.clicked.connect(self.reset.emit)
        self.updateScaledFactor(1.0)

        self._btnZoomOut = tool_btn(IconRegistry.minus_icon('lightgrey'), 'Zoom out', transparent_=True,
                                    parent=self)
        self._btnZoomOut.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self._btnZoomIn.clicked.connect(lambda: self.zoomed.emit(0.1))
        self._btnZoomOut.clicked.connect(lambda: self.zoomed.emit(-0.1))

        self.layout().addWidget(self._btnZoomOut)
        self.layout().addWidget(self._btnScaledFactor)
        self.layout().addWidget(self._btnZoomIn)

    def updateScaledFactor(self, scale: float):
        self._btnScaledFactor.setText(f'{int(scale * 100)}%')


class SecondarySelectorWidget(QFrame):
    selected = pyqtSignal(DiagramNodeType, str)

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

    def addWidget(self, widget: QWidget, row: int, col: int):
        self._grid.layout().addWidget(widget, row, col)

    def addButton(self, icon: QIcon, tooltip: str, row: int,
                  col: int) -> QToolButton:
        btn = tool_btn(icon, tooltip,
                       True, icon_resize=False,
                       properties=['transparent-rounded-bg-on-hover', 'top-selector'],
                       parent=self)
        self._btnGroup.addButton(btn)
        self._grid.layout().addWidget(btn, row, col)

        return btn

    def addItemTypeButton(self, itemType: DiagramNodeType, icon: QIcon, tooltip: str, row: int,
                          col: int, subType: str = '') -> QToolButton:
        def clicked(toggled: bool):
            if toggled:
                self.selected.emit(itemType, subType)

        btn = self.addButton(icon, tooltip, row, col)
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
