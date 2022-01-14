"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from typing import List

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QMenu, QWidgetAction, QPushButton

from src.main.python.plotlyst.view.common import decrease_font, OpacityEventFilter
from src.main.python.plotlyst.view.generated.grammar_popup_ui import Ui_GrammarPopup
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import FlowLayout


class GrammarPopup(QWidget, Ui_GrammarPopup):
    replacementRequested = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.wdgReplacements.setLayout(FlowLayout(margin=3, spacing=3))
        self.btnClose.setIcon(IconRegistry.close_icon())
        self.btnClose.installEventFilter(OpacityEventFilter(parent=self.btnClose))

    def init(self, replacements: List[str], msg: str, style: str):
        if style in ['misspelling']:
            self.lblType.setStyleSheet('color: #d90429;')
        elif style == 'style':
            self.lblType.setStyleSheet('color: #5e60ce;')
        else:
            self.lblType.setStyleSheet('color: #ffc300;')
        self.lblType.setText(style.capitalize())
        self.lblMessage.setText(msg)
        decrease_font(self.lblMessage)
        for i, replacement in enumerate(replacements):
            if i > 4:
                break
            self.wdgReplacements.layout().addWidget(self._button(replacement))

    def _button(self, replacement: str) -> QPushButton:
        btn = QPushButton(replacement, self)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet('''
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #4361ee, stop: 1 #4361ee);
                border: 1px solid #4361ee;
                border-radius: 5px;
                padding: 3px;
                color: white;
            }
        ''')
        btn.clicked.connect(lambda: self.replacementRequested.emit(replacement))

        return btn


class GrammarPopupMenu(QMenu):
    def __init__(self, parent=None):
        super(GrammarPopupMenu, self).__init__(parent)
        self._popupWidget = GrammarPopup(self)
        self._popupWidget.btnClose.clicked.connect(self.hide)
        self._popupWidget.replacementRequested.connect(self.hide)

    def popupWidget(self) -> GrammarPopup:
        return self._popupWidget

    def init(self, replacements: List[str], msg: str, style: str):
        action = QWidgetAction(self)

        self._popupWidget.init(replacements, msg, style)
        action.setDefaultWidget(self._popupWidget)
        self.addAction(action)
