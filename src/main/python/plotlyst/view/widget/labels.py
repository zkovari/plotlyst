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

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QFrame

from src.main.python.plotlyst.common import truncate_string
from src.main.python.plotlyst.core.domain import Character
from src.main.python.plotlyst.view.common import line
from src.main.python.plotlyst.view.icons import set_avatar, IconRegistry
from src.main.python.plotlyst.view.layout import FlowLayout


class Label(QFrame):
    pass


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

    def addLabel(self, label: Label):
        self.layout().addWidget(label)

    def clear(self):
        self.layout().clear()


class CharacterLabel(Label):
    def __init__(self, character: Character, pov: bool = False, parent=None):
        super(CharacterLabel, self).__init__(parent)
        self.character = character
        _layout = QHBoxLayout()
        _layout.setSpacing(2)
        _layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(_layout)
        self.lblAvatar = QLabel()
        set_avatar(self.lblAvatar, self.character, 24)
        _layout.addWidget(self.lblAvatar)
        _layout.addWidget(QLabel(truncate_string(character.name, 25)))

        role = self.character.role()
        if role:
            self.lblRole = QLabel()
            self.lblRole.setPixmap(IconRegistry.from_name(role.icon, role.icon_color).pixmap(QSize(24, 24)))
            _layout.addWidget(line(vertical=True))
            _layout.addWidget(self.lblRole)

        border_size = 3 if pov else 2
        border_color = '#3f7cac' if pov else '#bad7f2'

        self.setStyleSheet(f'''
        CharacterLabel {{
            border: {border_size}px solid {border_color}; 
            border-radius: 8px; padding-left: 3px; padding-right: 3px;}}
        ''')
