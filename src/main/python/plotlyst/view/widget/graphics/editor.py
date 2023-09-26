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
from typing import Optional, Any

from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon, QPaintEvent, QKeySequence, QShowEvent
from PyQt6.QtWidgets import QFrame, \
    QToolButton, QWidget, \
    QAbstractButton, QSlider, QButtonGroup, QPushButton, QLabel
from overrides import overrides
from qthandy import hbox, margins, sp, vbox, grid, pointy, vline, decr_icon, transparent, retain_when_hidden
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_TERTIARY_COLOR
from src.main.python.plotlyst.core.domain import DiagramNodeType, NODE_SUBTYPE_QUESTION, NODE_SUBTYPE_FORESHADOWING, \
    NODE_SUBTYPE_DISTURBANCE, NODE_SUBTYPE_CONFLICT, NODE_SUBTYPE_GOAL, NODE_SUBTYPE_BACKSTORY
from src.main.python.plotlyst.view.common import shadow, tool_btn, ExclusiveOptionalButtonGroup
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.graphics.items import EventItem, ConnectorItem
from src.main.python.plotlyst.view.widget.input import FontSizeSpinBox, AutoAdjustableLineEdit
from src.main.python.plotlyst.view.widget.utility import ColorPicker


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


class BaseItemToolbar(QWidget):
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


class TextLineEditorPopup(MenuWidget):

    def __init__(self, text: str, rect: QRect, parent=None, placeholder: str = 'Event'):
        super().__init__(parent)
        transparent(self)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._lineEdit = AutoAdjustableLineEdit(defaultWidth=rect.width())
        self._lineEdit.setPlaceholderText(placeholder)
        self._lineEdit.setText(text)
        self.addWidget(self._lineEdit)

        self._lineEdit.editingFinished.connect(self.hide)

    @overrides
    def showEvent(self, QShowEvent):
        self._lineEdit.setFocus()

    def text(self) -> str:
        return self._lineEdit.text()


class EventSelectorWidget(SecondarySelectorWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid.addWidget(QLabel('Events'), 0, 0, 1, 3)

        self._btnGeneral = self.addItemTypeButton(DiagramNodeType.EVENT,
                                                  IconRegistry.from_name('mdi.square-rounded-outline'),
                                                  'General event', 1, 0)
        self._btnGoal = self.addItemTypeButton(DiagramNodeType.EVENT, IconRegistry.goal_icon('black', 'black'),
                                               'Add new goal',
                                               1, 1, subType=NODE_SUBTYPE_GOAL)
        self._btnConflict = self.addItemTypeButton(DiagramNodeType.EVENT,
                                                   IconRegistry.conflict_icon('black', 'black'),
                                                   'Conflict', 1, 2, subType=NODE_SUBTYPE_CONFLICT)
        self._btnDisturbance = self.addItemTypeButton(DiagramNodeType.EVENT,
                                                      IconRegistry.inciting_incident_icon('black'),
                                                      'Inciting incident', 2,
                                                      0, subType=NODE_SUBTYPE_DISTURBANCE)
        self._btnBackstory = self.addItemTypeButton(DiagramNodeType.EVENT,
                                                    IconRegistry.backstory_icon('black', 'black'),
                                                    'Backstory', 2, 1, subType=NODE_SUBTYPE_BACKSTORY)

        self._grid.addWidget(QLabel('Narrative'), 3, 0, 1, 3)
        self._btnQuestion = self.addItemTypeButton(DiagramNodeType.SETUP, IconRegistry.from_name('ei.question-sign'),
                                                   "Reader's question", 4,
                                                   0, subType=NODE_SUBTYPE_QUESTION)
        self._btnSetup = self.addItemTypeButton(DiagramNodeType.SETUP, IconRegistry.from_name('ri.seedling-fill'),
                                                'Setup and payoff', 4, 1)
        self._btnForeshadowing = self.addItemTypeButton(DiagramNodeType.SETUP,
                                                        IconRegistry.from_name('mdi6.crystal-ball'),
                                                        'Foreshadowing',
                                                        4, 2, subType=NODE_SUBTYPE_FORESHADOWING)

        self._btnGeneral.setChecked(True)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        self._btnGeneral.setChecked(True)


class PaintedItemBasedToolbar(BaseItemToolbar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._item: Optional[Any] = None

        self._btnColor = tool_btn(IconRegistry.from_name('fa5s.circle', color='darkBlue'), 'Change style',
                                  transparent_=True)
        self._colorPicker = ColorPicker(self, maxColumn=5)
        self._colorPicker.colorPicked.connect(self._colorChanged)
        self._colorSecondaryWidget = SecondarySelectorWidget(self)
        self._colorSecondaryWidget.addWidget(self._colorPicker, 0, 0)
        self.addSecondaryWidget(self._btnColor, self._colorSecondaryWidget)
        self._btnIcon = tool_btn(IconRegistry.from_name('mdi.emoticon-outline'), 'Change icon', transparent_=True)
        self._btnIcon.clicked.connect(self._showIconSelector)

    def setItem(self, item: Any):
        self._item = None
        self._hideSecondarySelectors()

        icon: str = item.icon()
        self._updateColor(item.color().name())
        if icon:
            self._updateIcon(icon)
        else:
            self._resetIcon()

        self._item = item

    def _showIconSelector(self):
        dialog = IconSelectorDialog()
        retain_when_hidden(dialog.selector.colorPicker)
        dialog.selector.colorPicker.setVisible(False)
        result = dialog.display()
        if result and self._item:
            self._item.setIcon(result[0])
            self._updateIcon(result[0])

    def _colorChanged(self, color: QColor):
        if self._item:
            self._item.setColor(color)
            self._updateColor(color.name())
            pass

    def _updateIcon(self, icon: str):
        self._btnIcon.setIcon(IconRegistry.from_name(icon))

    def _resetIcon(self):
        self._btnIcon.setIcon(IconRegistry.from_name('mdi.emoticon-outline'))

    def _updateColor(self, color: str):
        self._btnColor.setIcon(IconRegistry.from_name('fa5s.circle', color))


class ConnectorToolbar(PaintedItemBasedToolbar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._btnRelationType = RelationsButton()

        self._solidLine = SolidPenStyleSelector()
        self._dashLine = DashPenStyleSelector()
        self._dotLine = DotPenStyleSelector()
        self._lineBtnGroup = QButtonGroup()
        self._lineBtnGroup.addButton(self._solidLine)
        self._lineBtnGroup.addButton(self._dashLine)
        self._lineBtnGroup.addButton(self._dotLine)
        self._lineBtnGroup.buttonClicked.connect(self._penStyleChanged)

        self._sbWidth = PenWidthEditor()
        self._sbWidth.valueChanged.connect(self._widthChanged)

        self._toolbar.layout().addWidget(self._btnRelationType)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._btnColor)
        self._toolbar.layout().addWidget(self._btnIcon)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._solidLine)
        self._toolbar.layout().addWidget(self._dashLine)
        self._toolbar.layout().addWidget(self._dotLine)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._sbWidth)

    @overrides
    def setItem(self, connector: ConnectorItem):
        super().setItem(connector)
        self._item = None

        self._sbWidth.setValue(connector.penWidth())

        penStyle = connector.penStyle()
        for line in [self._solidLine, self._dashLine, self._dotLine]:
            if penStyle == line.penStyle():
                line.setChecked(True)
                break
        self._item = connector

    def _penStyleChanged(self):
        btn = self._lineBtnGroup.checkedButton()
        if btn and self._item:
            self._item.setPenStyle(btn.penStyle())

    def _widthChanged(self, value: int):
        if self._item:
            self._item.setPenWidth(value)


class EventItemToolbar(PaintedItemBasedToolbar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._btnType = tool_btn(IconRegistry.from_name('mdi.square-rounded-outline'), 'Change type', transparent_=True)
        self._sbFont = FontSizeSpinBox()
        self._sbFont.fontChanged.connect(self._fontChanged)
        self._btnBold = tool_btn(IconRegistry.from_name('fa5s.bold'), 'Bold', checkable=True, icon_resize=False,
                                 properties=['transparent-rounded-bg-on-hover', 'top-selector'])
        decr_icon(self._btnBold)
        self._btnItalic = tool_btn(IconRegistry.from_name('fa5s.italic'), 'Italic',
                                   checkable=True, icon_resize=False,
                                   properties=['transparent-rounded-bg-on-hover', 'top-selector'])
        decr_icon(self._btnItalic)
        self._btnUnderline = tool_btn(IconRegistry.from_name('fa5s.underline'), 'Underline',
                                      checkable=True, icon_resize=False,
                                      properties=['transparent-rounded-bg-on-hover', 'top-selector'])
        decr_icon(self._btnUnderline)
        self._btnBold.clicked.connect(self._textStyleChanged)
        self._btnItalic.clicked.connect(self._textStyleChanged)
        self._btnUnderline.clicked.connect(self._textStyleChanged)

        self._eventSelector = EventSelectorWidget(self)
        self.addSecondaryWidget(self._btnType, self._eventSelector)
        self._eventSelector.selected.connect(self._typeChanged)

        self._toolbar.layout().addWidget(self._btnType)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._btnColor)
        self._toolbar.layout().addWidget(self._btnIcon)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._sbFont)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(group(self._btnBold, self._btnItalic, self._btnUnderline, margin=0, spacing=2))

    @overrides
    def setItem(self, item: EventItem):
        super().setItem(item)
        self._item = None

        self._sbFont.setValue(item.fontSize())
        self._btnBold.setChecked(item.bold())
        self._btnItalic.setChecked(item.italic())
        self._btnUnderline.setChecked(item.underline())

        self._item = item

    def _fontChanged(self, size: int):
        self._hideSecondarySelectors()
        if self._item:
            self._item.setFontSettings(size=size)

    def _textStyleChanged(self):
        self._hideSecondarySelectors()
        if self._item:
            self._item.setFontSettings(bold=self._btnBold.isChecked(), italic=self._btnItalic.isChecked(),
                                       underline=self._btnUnderline.isChecked())

    def _typeChanged(self, itemType: DiagramNodeType):
        if self._item:
            self._item.setItemType(itemType)


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
