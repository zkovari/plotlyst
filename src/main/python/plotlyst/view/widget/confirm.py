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

from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QDialog, QWidget, QApplication
from overrides import overrides
from qthandy import vbox, line, hbox, sp, vspacer

from src.main.python.plotlyst.view.common import label, push_btn, frame, shadow, tool_btn
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.display import OverlayWidget


@dataclass
class ConfirmationResult:
    confirmed: bool


class ConfirmationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        vbox(self)
        self.frame = frame()
        self.frame.setProperty('relaxed-white-bg', True)
        self.frame.setProperty('large-rounded', True)
        vbox(self.frame, 10, 10)
        self.layout().addWidget(self.frame)
        self.setMinimumSize(200, 150)
        shadow(self.frame)

        self.title = label('Confirm', h4=True)
        self.btnReset = tool_btn(IconRegistry.close_icon('grey'), tooltip='Cancel', transparent_=True)
        self.btnReset.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btnReset.setIconSize(QSize(12, 12))
        self.btnReset.clicked.connect(self.reject)
        sp(self.title).v_max()
        self.wdgTitle = QWidget()
        hbox(self.wdgTitle)
        self.wdgTitle.layout().addWidget(self.title, alignment=Qt.AlignmentFlag.AlignLeft)
        self.wdgTitle.layout().addWidget(self.btnReset, alignment=Qt.AlignmentFlag.AlignRight)
        self.text = label('Do you confirm?', wordWrap=True)
        self.btnConfirm = push_btn(text='Confirm', properties=['base', 'deconstructive'])
        sp(self.btnConfirm).h_exp()
        self.btnConfirm.clicked.connect(self.accept)
        self.btnConfirm.setFocus()

        self.frame.layout().addWidget(self.wdgTitle)
        self.frame.layout().addWidget(line())
        self.frame.layout().addWidget(self.text)
        self.frame.layout().addWidget(vspacer())
        self.frame.layout().addWidget(self.btnConfirm)

    def display(self) -> ConfirmationResult:
        result = self.exec()

        if result == QDialog.DialogCode.Accepted:
            return ConfirmationResult(True)

        return ConfirmationResult(False)

    @overrides
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()


def confirmed(message: str, title: str = 'Confirm?') -> bool:
    dialog = ConfirmationDialog()
    dialog.title.setText(title)
    dialog.text.setText(message)

    window = QApplication.activeWindow()
    overlay = OverlayWidget(window)
    overlay.show()

    center = window.frameGeometry().center()
    dialog.move(window.frameGeometry().center() - QPoint(dialog.sizeHint().width() // 2, dialog.sizeHint().height() // 2))

    result = dialog.display().confirmed

    overlay.setHidden(True)

    return result
