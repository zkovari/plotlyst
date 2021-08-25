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
import emoji
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtWidgets import QFrame
from fbs_runtime import platform
from overrides import overrides

from src.main.python.plotlyst.common import PIVOTAL_COLOR
from src.main.python.plotlyst.core.domain import NovelDescriptor, Character, Scene, ACTION_SCENE, REACTION_SCENE
from src.main.python.plotlyst.view.common import emoji_font
from src.main.python.plotlyst.view.generated.character_card_ui import Ui_CharacterCard
from src.main.python.plotlyst.view.generated.novel_card_ui import Ui_NovelCard
from src.main.python.plotlyst.view.generated.scene_card_ui import Ui_SceneCard
from src.main.python.plotlyst.view.icons import IconRegistry, set_avatar
from src.main.python.plotlyst.view.widget.labels import CharacterAvatarLabel


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
        border_color = self._borderColor(selected)
        border_size = self._borderSize(selected)
        background_color = self._bgColor(selected)
        self.setStyleSheet(f'''
           QFrame[mainFrame=true] {{
               border: {border_size}px solid {border_color};
               border-radius: 15px;
               background-color: {background_color};
           }}''')

    def _bgColor(self, selected: bool = False) -> str:
        return '#dec3c3' if selected else '#f9f4f4'

    def _borderSize(self, selected: bool = False) -> int:
        return 4 if selected else 2

    def _borderColor(self, selected: bool = False) -> str:
        return '#2a4d69' if selected else '#adcbe3'


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


class SceneCard(Ui_SceneCard, _Card):
    def __init__(self, scene: Scene, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.scene = scene

        self.wdgCharacters.layout().setSpacing(1)

        self.textTitle.setText(self.scene.title)
        self.textTitle.setAlignment(Qt.AlignCenter)
        if scene.pov:
            set_avatar(self.lblPov, scene.pov, 64)
        else:
            self.lblPov.clear()
            self.lblPov.setHidden(True)
        for char in scene.characters:
            self.wdgCharacters.addLabel(CharacterAvatarLabel(char))

        if self.scene.beat:
            self.lblBeat.clear()
            # self.lblBeat.setText(self.scene.beat.text)
            if platform.is_windows():
                self._emoji_font = emoji_font(14)
            else:
                self._emoji_font = emoji_font(20)
            self.lblBeatEmoji.setFont(self._emoji_font)
            self.lblBeatEmoji.setText(emoji.emojize(':performing_arts:'))
        else:
            self.lblBeat.clear()
            self.lblBeat.setHidden(True)
            self.lblBeatEmoji.clear()
            self.lblBeatEmoji.setHidden(True)

        if scene.notes:
            self.btnComments.setIcon(IconRegistry.from_name('fa5s.comment', color='#4f5d75'))
        else:
            self.btnComments.setHidden(True)

        if self.scene.type == ACTION_SCENE:
            self.lblType.setPixmap(IconRegistry.action_scene_icon().pixmap(QSize(24, 24, )))
        elif self.scene.type == REACTION_SCENE:
            self.lblType.setPixmap(IconRegistry.reaction_scene_icon().pixmap(QSize(24, 24, )))
        else:
            self.lblType.clear()

        self._setStyleSheet()

    @overrides
    def _bgColor(self, selected: bool = False) -> str:
        if self.scene.beat:
            return '#8eaf9d' if selected else '#a6d8d4'
        return super(SceneCard, self)._bgColor(selected)

    @overrides
    def _borderSize(self, selected: bool = False) -> int:
        if self.scene.beat:
            return 7 if selected else 5
        return super(SceneCard, self)._borderSize(selected)

    @overrides
    def _borderColor(self, selected: bool = False) -> str:
        if self.scene.beat:
            return '#6b7d7d' if selected else PIVOTAL_COLOR
        return super(SceneCard, self)._borderColor(selected)
