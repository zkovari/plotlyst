"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTextEdit


class AutoAdjustableTextEdit(QTextEdit):
    def __init__(self, parent=None, height: int = 40):
        super(AutoAdjustableTextEdit, self).__init__(parent)
        self.textChanged.connect(self._resizeToContent)
        self._minHeight = height
        self.setMaximumHeight(self._minHeight)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def _resizeToContent(self):
        size = self.document().size()
        self.setMaximumHeight(max(self._minHeight, size.height()))
