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
import math

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QLabel

from src.main.python.plotlyst.common import truncate_string
from src.main.python.plotlyst.view.layout import FlowLayout


class LabelsWidget(QWidget):

    def __init__(self, parent=None):
        super(LabelsWidget, self).__init__(parent)
        self.setLayout(FlowLayout())

    def addText(self, text: str, color: str):
        label = QLabel(truncate_string(text, 40))
        rgb = QColor(color).getRgb()
        r = rgb[0]
        g = rgb[1]
        b = rgb[2]
        hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
        text_color = 'black' if hsp > 127.5 else 'white'
        label.setStyleSheet(
            f'''QLabel {{
                background-color: {color}; border-radius: 6px; color: {text_color};
                padding-left: 3px; padding-right: 3px;
            }}''')

        self.layout().addWidget(label)

    def clear(self):
        self.layout().clear()
