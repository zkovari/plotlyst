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
from dataclasses import dataclass

import overrides
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QDialog, QWidget, QFrame
from overrides import overrides
from qthandy import vbox, line, hbox, sp

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.view.common import label, push_btn, frame, shadow


@dataclass
class ConfirmationResult:
    confirmed: bool


class ConfirmationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        vbox(self)
        self.frame = frame()
        self.frame.setProperty('relaxed-white-bg', True)
        self.frame.setProperty('large-rounded', True)
        vbox(self.frame, 5, 5)
        self.layout().addWidget(self.frame)
        self.setMinimumSize(200, 150)
        shadow(self.frame)

        self.title = label('Confirm', h4=True)
        sp(self.title).v_max()
        self.text = label('Do you conform?', wordWrap=True)
        self.btnConfirm = push_btn(text='Confirm')
        # self.btnCancel = push_btn(text='Cancel')
        #
        # self.wdgButton = QWidget()
        # hbox(self.wdgButton)

        self.frame.layout().addWidget(self.title)
        self.frame.layout().addWidget(line())
        self.frame.layout().addWidget(self.text)
        self.frame.layout().addWidget(self.btnConfirm, alignment=Qt.AlignmentFlag.AlignRight)

    def display(self) -> ConfirmationResult:
        result = self.exec()

        if result == QDialog.DialogCode.Accepted:
            return ConfirmationResult(True)

        return ConfirmationResult(False)

    @overrides
    def closeEvent(self, event: QCloseEvent) -> None:
        print(event)
        event.accept()


def confirmed(message: str) -> bool:
    return ConfirmationDialog().display().confirmed
