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
from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QWidget
from qthandy import line, hbox, sp, vspacer

from plotlyst.view.common import label, push_btn
from plotlyst.view.layout import group
from plotlyst.view.widget.display import PopupDialog


@dataclass
class ConfirmationResult:
    confirmed: bool


class BaseDialog(PopupDialog):
    def __init__(self, message: str, title: str = 'Confirm?', parent=None):
        super().__init__(parent)
        self.title = label(title, h4=True)
        sp(self.title).v_max()
        self.wdgTitle = QWidget()
        hbox(self.wdgTitle, spacing=5)
        self.wdgTitle.layout().addWidget(self.title, alignment=Qt.AlignmentFlag.AlignLeft)
        self.wdgTitle.layout().addWidget(self.btnReset, alignment=Qt.AlignmentFlag.AlignRight)
        self.text = label(message, wordWrap=True)

        self.frame.layout().addWidget(self.wdgTitle)
        self.frame.layout().addWidget(line())
        self.frame.layout().addWidget(self.text)
        self.frame.layout().addWidget(vspacer())

    def display(self) -> ConfirmationResult:
        result = self.exec()

        if result == QDialog.DialogCode.Accepted:
            return ConfirmationResult(True)

        return ConfirmationResult(False)


class ConfirmationDialog(BaseDialog):
    def __init__(self, message: str, title: str = 'Confirm?', parent=None):
        super().__init__(message, title, parent)

        self.btnConfirm = push_btn(text='Confirm', properties=['base', 'deconstructive'])
        sp(self.btnConfirm).h_exp()
        self.btnConfirm.clicked.connect(self.accept)
        self.btnConfirm.setFocus()

        self.frame.layout().addWidget(self.btnConfirm)

    @classmethod
    def confirm(cls, message: str, title: str = 'Confirm?') -> bool:
        return cls.popup(message, title).confirmed


class QuestionDialog(BaseDialog):
    def __init__(self, message: str, title: str, btnConfirmText: str, btnCancelText: str,
                 parent=None):
        super().__init__(message, title, parent)

        self.btnConfirm = push_btn(text=btnConfirmText, properties=['base', 'positive'])
        self.btnConfirm.clicked.connect(self.accept)
        self.btnCancel = push_btn(text=btnCancelText, base=True)
        self.btnCancel.clicked.connect(self.reject)
        self.btnCancel.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btnConfirm.setFocus()

        self.frame.layout().addWidget(group(self.btnCancel, self.btnConfirm))

    @classmethod
    def ask(cls, message: str, title: str, btnConfirmText: str, btnCancelText: str) -> bool:
        return cls.popup(message, title, btnConfirmText, btnCancelText).confirmed


def confirmed(message: str, title: str = 'Confirm?') -> bool:
    return ConfirmationDialog.confirm(message, title)


def asked(message: str, title: str, btnConfirmText: str = 'Confirm', btnCancelText: str = 'Cancel') -> bool:
    return QuestionDialog.ask(message, title, btnConfirmText, btnCancelText)
