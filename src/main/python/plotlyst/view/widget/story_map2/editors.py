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

from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QEnterEvent
from PyQt6.QtWidgets import QWidget, QTextEdit
from overrides import overrides
from qthandy import hbox, margins


class StickerEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = QTextEdit()
        self._text.setProperty('relaxed-white-bg', True)
        self._text.setProperty('rounded', True)
        self._text.setPlaceholderText('Leave a comment')

        hbox(self).addWidget(self._text)
        margins(self, left=3)

        self.setFixedSize(200, 200)

    def setText(self, text: str):
        self._text.setText(text)

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        self.setVisible(True)
        self._text.setFocus()

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self.setHidden(True)
