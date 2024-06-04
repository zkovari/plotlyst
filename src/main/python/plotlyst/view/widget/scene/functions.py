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
from typing import Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget
from overrides import overrides
from qthandy import vbox, incr_icon, incr_font, bold, flow, margins, vspacer, retain_when_hidden, spacer
from qthandy.filter import OpacityEventFilter, VisibilityToggleEventFilter

from plotlyst.common import PLOTLYST_SECONDARY_COLOR
from plotlyst.core.domain import Scene, OutlineItem, LayoutType
from plotlyst.view.common import push_btn, frame
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.widget.display import IconText
from plotlyst.view.widget.input import RemovalButton
from plotlyst.view.widget.outline import OutlineTimelineWidget, OutlineItemWidget


class ScenePrimaryFunctionWidget(OutlineItemWidget):
    SceneFunctionMimeType: str = 'application/scene-function'

    functionEdited = pyqtSignal()

    def __init__(self, item: OutlineItem, parent=None):
        super().__init__(item, parent)

        # vbox(self)
        # self._label = QPushButton()
        # transparent(self._label)
        # bold(self._label)
        # self._label.setText('Function')
        # # self._label.setIcon(principle_icon(principle.type))
        # self._label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # # self._label.setCheckable(True)
        # # self._label.setChecked(True)
        #
        # self._textedit = QTextEdit(self)
        # self._textedit.setProperty('white-bg', True)
        # self._textedit.setProperty('rounded', True)
        # # hint = principle_placeholder(principle.type, plotType)
        # self._textedit.setPlaceholderText('Define primary function')
        # # self._textedit.setToolTip(hint)
        # self._textedit.setTabChangesFocus(True)
        # if app_env.is_mac():
        #     incr_font(self._textedit)
        # # self._textedit.setText(principle.value)
        # self._textedit.setMinimumSize(175, 100)
        # self._textedit.setMaximumSize(190, 120)
        # self._textedit.verticalScrollBar().setVisible(False)
        # # if plotType != PlotType.Internal and principle.type in internal_principles:
        # #     shadow(self._textedit, color=QColor(CONFLICT_SELF_COLOR))
        # # else:
        # #     shadow(self._textedit)
        # self._textedit.textChanged.connect(self._valueChanged)
        #
        # self.layout().addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)
        # self.layout().addWidget(self._textedit)

    @overrides
    def mimeType(self):
        return self.SceneFunctionMimeType

    def _valueChanged(self):
        pass


class EventCauseFunctionWidget(OutlineTimelineWidget):
    def __init__(self, parent=None):
        super().__init__(parent, paintTimeline=True, framed=False, layout=LayoutType.HORIZONTAL)
        # self.setProperty('relaxed-white-bg', True)
        # self.setProperty('large-rounded', True)
        margins(self, 0, 0, 0, 0)
        self.layout().setSpacing(0)

        # self._menu = DynamicPlotPrincipleSelectorMenu(groupType)
        # self._menu.selected.connect(self._insertPrinciple)

    @overrides
    def _newBeatWidget(self, item: OutlineItem) -> OutlineItemWidget:
        wdg = ScenePrimaryFunctionWidget(item)
        wdg.removed.connect(self._beatRemoved)
        return wdg

    @overrides
    def _newPlaceholderWidget(self, displayText: bool = False) -> QWidget:
        wdg = super()._newPlaceholderWidget(displayText)
        margins(wdg, top=2)
        if displayText:
            wdg.btn.setText('Insert element')
        wdg.btn.setToolTip('Insert new element')
        return wdg

    @overrides
    def _placeholderClicked(self, placeholder: QWidget):
        self._currentPlaceholder = placeholder
        item = OutlineItem()
        widget = self._newBeatWidget(item)
        self._insertWidget(item, widget)
        # self._menu.exec(self.mapToGlobal(self._currentPlaceholder.pos()))

    # def _insertPrinciple(self, principleType: DynamicPlotPrincipleType):
    #     item = DynamicPlotPrinciple(type=principleType)
    #
    #     widget = self._newBeatWidget(item)
    #     self._insertWidget(item, widget)


class EventCauseFunctionGroupWidget(QWidget):
    remove = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame = frame()
        self.frame.setObjectName('frame')
        vbox(self.frame, 0, 0)

        self.setStyleSheet(f'''
                                #frame {{
                                    border: 0px;
                                    border-top: 2px solid {PLOTLYST_SECONDARY_COLOR};
                                    border-radius: 15px;
                                }}''')

        vbox(self)
        self._wdgPrinciples = EventCauseFunctionWidget()
        self._wdgPrinciples.setStructure([])

        self._title = IconText()
        self._title.setText('Cause and effect')
        # self._title.setIcon(IconRegistry.from_name(self.group.type.icon(), self.group.type.color()))
        incr_icon(self._title, 4)
        bold(self._title)
        # apply_button_palette_color(self._title, self.group.type.color())

        self.btnRemove = RemovalButton()
        retain_when_hidden(self.btnRemove)
        self.installEventFilter(VisibilityToggleEventFilter(self.btnRemove, self))
        self.btnRemove.clicked.connect(self.remove)

        self.frame.layout().addWidget(self._wdgPrinciples)
        self.layout().addWidget(group(spacer(), self._title, spacer(), self.btnRemove))
        self.layout().addWidget(self.frame)


class SceneFunctionsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene: Optional[Scene] = None

        vbox(self)
        self.btnPrimary = push_btn(IconRegistry.from_name('mdi6.note-text-outline', 'grey'), 'Primary',
                                   transparent_=True)
        incr_icon(self.btnPrimary, 2)
        incr_font(self.btnPrimary, 2)
        self.btnPrimary.installEventFilter(OpacityEventFilter(self.btnPrimary, leaveOpacity=0.7))
        self.btnPrimary.clicked.connect(self._addPrimary)

        self.btnSecondary = push_btn(IconRegistry.from_name('fa5s.list', 'grey'), 'Secondary',
                                     transparent_=True)
        self.btnSecondary.installEventFilter(OpacityEventFilter(self.btnSecondary, leaveOpacity=0.7))
        incr_icon(self.btnSecondary, 1)
        incr_font(self.btnSecondary, 1)

        self.wdgPrimary = QWidget()
        flow(self.wdgPrimary)
        # vbox(self.wdgPrimary)
        margins(self.wdgPrimary, left=20)

        self.layout().addWidget(self.btnPrimary, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.wdgPrimary)
        self.layout().addWidget(self.btnSecondary, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(vspacer())

    def setScene(self, scene: Scene):
        self._scene = scene

    def _addPrimary(self):
        wdg = EventCauseFunctionGroupWidget()
        # wdg = EventCauseFunctionWidget()
        # wdg.setStructure([])
        self.wdgPrimary.layout().addWidget(wdg)
