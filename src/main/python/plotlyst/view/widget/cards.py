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
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtWidgets import QFrame
from overrides import overrides

from src.main.python.plotlyst.core.domain import NovelDescriptor, Character
from src.main.python.plotlyst.view.generated.character_card_ui import Ui_CharacterCard
from src.main.python.plotlyst.view.generated.novel_card_ui import Ui_NovelCard
from src.main.python.plotlyst.view.icons import IconRegistry, set_avatar


class _Card(QFrame):
    selected = pyqtSignal(object)
    doubleClicked = pyqtSignal(object)

    @overrides
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self._setStyleSheet(selected=True)
        self.selected.emit(self)

    @overrides
    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        self._setStyleSheet(selected=True)
        self.selected.emit(self)
        self.doubleClicked.emit(self)

    def clearSelection(self):
        self._setStyleSheet()

    def _setStyleSheet(self, selected: bool = False):
        border_color = '#2a4d69' if selected else '#adcbe3'
        border_size = 4 if selected else 2
        background_color = '#dec3c3' if selected else '#f9f4f4'
        self.setStyleSheet(f'''
           QFrame[mainFrame=true] {{
               border: {border_size}px solid {border_color};
               border-radius: 15px;
               background-color: {background_color};
           }}''')


class NovelCard(Ui_NovelCard, _Card):

    def __init__(self, novel: NovelDescriptor, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.label.setText(self.novel.title)
        self._setStyleSheet()

    def refresh(self):
        self.label.setText(self.novel.title)


class CharacterCard(Ui_CharacterCard, _Card):

    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.character = character
        self.lblName.setText(self.character.name)
        set_avatar(self.lblPic, self.character)

        enneagram = self.character.enneagram()
        if enneagram:
            self.lblEnneagram.setPixmap(
                IconRegistry.from_name(enneagram.icon, enneagram.icon_color).pixmap(QSize(28, 28)))
        role = self.character.role()
        if role:
            self.lblRole.setPixmap(IconRegistry.from_name(role.icon, role.icon_color).pixmap(QSize(24, 24)))
        self._setStyleSheet()
