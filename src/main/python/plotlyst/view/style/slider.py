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
QSlider::groove:horizontal {
    border: 1px solid #999999;
    height: 6px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
    margin: 0px 0;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4B0763, stop:1 #4B0763);
    border: 1px solid #4B0763;
    width: 15px;
    margin: -3px -1px;
    border-radius: 3px;
}
'''


def apply_slider_color(wdg: QWidget, color: Union[str, QColor, Qt.GlobalColor]):
    if isinstance(color, QColor):
        color = color.name()
    wdg.setStyleSheet(f'''
                QSlider::add-page:horizontal {{
                    background: lightgray;
                }}
                QSlider::sub-page:horizontal {{
                    background: {color};
                }}
            ''')
