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
from typing import Union

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QFrame, QToolButton

from src.main.python.plotlyst.common import truncate_string
from src.main.python.plotlyst.core.domain import Character, Conflict, ConflictType
from src.main.python.plotlyst.view.common import line
from src.main.python.plotlyst.view.icons import set_avatar, IconRegistry, avatars
from src.main.python.plotlyst.view.layout import FlowLayout


class Label(QFrame):
    def __init__(self, parent=None):
        super(Label, self).__init__(parent)
        _layout = QHBoxLayout()
        _layout.setSpacing(2)
        _layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(_layout)


class LabelsWidget(QWidget):

    def __init__(self, parent=None):
        super(LabelsWidget, self).__init__(parent)
        self.setLayout(FlowLayout(margin=1, spacing=4))

    def addText(self, text: str, color: str = '#7c98b3'):
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

    def addLabel(self, label: Union[Label, QLabel]):
        self.layout().addWidget(label)

    def clear(self):
        self.layout().clear()


class CharacterLabel(Label):
    def __init__(self, character: Character, pov: bool = False, parent=None):
        super(CharacterLabel, self).__init__(parent)
        self.character = character
        # self.lblAvatar = QLabel()
        self.btnAvatar = QToolButton()
        self.btnAvatar.setStyleSheet('border: 0px;')
        # set_avatar(self.lblAvatar, self.character, 24)
        self.btnAvatar.setIcon(QIcon(avatars.pixmap(self.character)))
        self.btnAvatar.setIconSize(QSize(24, 24))
        # self.layout().addWidget(self.lblAvatar)
        self.layout().addWidget(self.btnAvatar)
        self.layout().addWidget(QLabel(truncate_string(character.name)))

        role = self.character.role()
        if role:
            self.lblRole = QLabel()
            self.lblRole.setPixmap(IconRegistry.from_name(role.icon, role.icon_color).pixmap(QSize(24, 24)))
            self.layout().addWidget(line(vertical=True))
            self.layout().addWidget(self.lblRole)

        border_size = 3 if pov else 2
        border_color = '#3f7cac' if pov else '#bad7f2'

        self.setStyleSheet(f'''
        CharacterLabel {{
            border: {border_size}px solid {border_color}; 
            border-radius: 8px; padding-left: 3px; padding-right: 3px;}}
        ''')


class CharacterAvatarLabel(QToolButton):
    def __init__(self, character: Character, size: int = 24, parent=None):
        super(CharacterAvatarLabel, self).__init__(parent)
        self.setStyleSheet('border: 0px;')
        # set_avatar(self.lblAvatar, self.character, 24)
        self.setIcon(QIcon(avatars.pixmap(character)))
        self.setIconSize(QSize(size, size))


class ConflictLabel(Label):
    def __init__(self, conflict: Conflict, parent=None):
        super(ConflictLabel, self).__init__(parent)
        self.conflict = conflict

        self.lblConflict = QLabel()
        self.lblConflict.setPixmap(IconRegistry.conflict_icon().pixmap(QSize(24, 24)))
        self.layout().addWidget(self.lblConflict)

        self.lblAvatar = QLabel()
        if self.conflict.character:
            set_avatar(self.lblAvatar, self.conflict.character, 24)
        else:
            if self.conflict.type == ConflictType.CHARACTER:
                icon = IconRegistry.conflict_character_icon()
            elif self.conflict.type == ConflictType.SOCIETY:
                icon = IconRegistry.conflict_society_icon()
            elif self.conflict.type == ConflictType.NATURE:
                icon = IconRegistry.conflict_nature_icon()
            elif self.conflict.type == ConflictType.TECHNOLOGY:
                icon = IconRegistry.conflict_technology_icon()
            elif self.conflict.type == ConflictType.SUPERNATURAL:
                icon = IconRegistry.conflict_supernatural_icon()
            elif self.conflict.type == ConflictType.SELF:
                icon = IconRegistry.conflict_self_icon()
            else:
                icon = IconRegistry.conflict_icon()
            self.lblAvatar.setPixmap(icon.pixmap(QSize(24, 24)))
        self.layout().addWidget(self.lblAvatar)
        self.layout().addWidget(QLabel(self.conflict.keyphrase))

        self.setStyleSheet('''
                ConflictLabel {
                    border: 2px solid #f3a712;
                    border-radius: 8px; padding-left: 3px; padding-right: 3px;}
                ''')


class TraitLabel(QLabel):
    def __init__(self, trait: str, positive: bool = True, parent=None):
        super(TraitLabel, self).__init__(parent)

        self.setText(trait)

        if positive:
            bg_color = '#519872'
            border_color = '#034732'
        else:
            bg_color = '#db5461'
            border_color = '#ef2917'
        self.setStyleSheet(f'''TraitLabel {{
            background-color: {bg_color};
            border: 2px solid {border_color};
            border-radius: 8px;
            color: white;
            padding-left: 0px; padding-right: 0px; padding-top: 0px; padding-bottom: 0px;
        }}''')
