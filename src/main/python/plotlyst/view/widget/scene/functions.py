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
from PyQt6.QtWidgets import QWidget, QTextEdit, QPushButton
from qthandy import vbox, incr_icon, incr_font, transparent, bold, flow, margins, vspacer
from qthandy.filter import OpacityEventFilter

from plotlyst.core.domain import Scene
from plotlyst.env import app_env
from plotlyst.view.common import push_btn
from plotlyst.view.icons import IconRegistry


class ScenePrimaryFunctionWidget(QWidget):
    functionEdited = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        vbox(self)
        self._label = QPushButton()
        transparent(self._label)
        bold(self._label)
        self._label.setText('Function')
        # self._label.setIcon(principle_icon(principle.type))
        self._label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self._label.setCheckable(True)
        # self._label.setChecked(True)

        self._textedit = QTextEdit(self)
        self._textedit.setProperty('white-bg', True)
        self._textedit.setProperty('rounded', True)
        # hint = principle_placeholder(principle.type, plotType)
        self._textedit.setPlaceholderText('Define primary function')
        # self._textedit.setToolTip(hint)
        self._textedit.setTabChangesFocus(True)
        if app_env.is_mac():
            incr_font(self._textedit)
        # self._textedit.setText(principle.value)
        self._textedit.setMinimumSize(175, 100)
        self._textedit.setMaximumSize(190, 120)
        self._textedit.verticalScrollBar().setVisible(False)
        # if plotType != PlotType.Internal and principle.type in internal_principles:
        #     shadow(self._textedit, color=QColor(CONFLICT_SELF_COLOR))
        # else:
        #     shadow(self._textedit)
        self._textedit.textChanged.connect(self._valueChanged)

        self.layout().addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._textedit)

    def _valueChanged(self):
        pass


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
        margins(self.wdgPrimary, left=20)

        self.layout().addWidget(self.btnPrimary, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.wdgPrimary)
        self.layout().addWidget(self.btnSecondary, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(vspacer())

    def setScene(self, scene: Scene):
        self._scene = scene

    def _addPrimary(self):
        wdg = ScenePrimaryFunctionWidget()
        self.wdgPrimary.layout().addWidget(wdg)
