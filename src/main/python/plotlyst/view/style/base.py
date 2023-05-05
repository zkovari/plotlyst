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
from typing import Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget

style = '''
* {
    icon-size: 20px;
}

QToolTip {
    border: 0px;
    font-size: 14pt;
    padding: 5px;
}

QToolBar {
    spacing: 1px;
}

.QWidget[white-bg=true] {
    background-color: white;
}

.QWidget[relaxed-white-bg=true] {
    background-color: #f8f9fa;
}

.QFrame[relaxed-white-bg=true] {
    background-color: #f8f9fa;
}

QDialog[relaxed-white-bg] {
    background-color: #f8f9fa;
}

'''


def apply_color(wdg: QWidget, color: Union[str, QColor, Qt.GlobalColor]):
    if isinstance(color, QColor):
        color = color.name()
    wdg.setStyleSheet(f'color: {color}')


def apply_bg_image(wdg: QWidget, resource_url: str):
    wdg.setStyleSheet(f'QWidget[bg-image=true] {{background-image: url({resource_url});}}')
