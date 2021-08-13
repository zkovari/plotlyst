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
from typing import Optional

import emoji
from PyQt5.QtCore import Qt, QByteArray, QBuffer, QIODevice, QSize
from PyQt5.QtGui import QImageReader, QImage
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QHBoxLayout
from fbs_runtime import platform

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel, Character
from src.main.python.plotlyst.view.common import emoji_font, spacer_widget
from src.main.python.plotlyst.view.generated.character_editor_ui import Ui_CharacterEditor
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.template import TemplateProfileView


class CharacterEditor:

    def __init__(self, novel: Novel, character: Optional[Character] = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_CharacterEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel

        if character:
            self.character = character
            self.ui.lineName.setText(self.character.name)
            self._new_character = False
        else:
            self.character = Character('')
            self._new_character = True

        if platform.is_windows():
            self._emoji_font = emoji_font(14)
        else:
            self._emoji_font = emoji_font(20)
        self.ui.lblNameEmoji.setFont(self._emoji_font)
        self.ui.lblNameEmoji.setText(emoji.emojize(':bust_in_silhouette:'))

        self.profile = TemplateProfileView(self.novel.character_profiles[0])
        self._profile_container = QWidget()
        self._profile_container.setLayout(QHBoxLayout())
        self._profile_container.layout().addWidget(self.profile)
        self._profile_container.layout().addWidget(spacer_widget())
        self.ui.wdgProfile.layout().insertWidget(0, self._profile_container)

        self.ui.btnUploadAvatar.setIcon(IconRegistry.upload_icon())
        self.ui.btnUploadAvatar.clicked.connect(self._upload_avatar)
        self.ui.btnClose.setIcon(IconRegistry.return_icon())
        self.ui.btnClose.clicked.connect(self._save)

        self._update_avatar()

    def _upload_avatar(self):
        filename: str = QFileDialog.getOpenFileName(None, 'Choose an image', '', 'Images (*.png *.jpg *jpeg)')
        if not filename:
            return
        reader = QImageReader(filename[0])
        reader.setAutoTransform(True)
        image: QImage = reader.read()
        if image is None:
            QMessageBox.warning(self.widget, 'Error while uploading image', 'Could not upload image')
            return
        array = QByteArray()
        buffer = QBuffer(array)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, 'PNG')
        self.character.avatar = array

        avatars.update(self.character)
        self._update_avatar()
        self._save()

    def _update_avatar(self):
        if self.character.avatar:
            self.ui.lblAvatar.setPixmap(
                avatars.pixmap(self.character).scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.ui.lblAvatar.setPixmap(IconRegistry.portrait_icon().pixmap(QSize(256, 256)))

    def _save(self):
        name = self.ui.lineName.text()
        if not name:
            return
        self.character.name = name
        if self._new_character:
            self.novel.characters.append(self.character)
            client.insert_character(self.novel, self.character)
        else:
            client.update_character(self.character)
        self._new_character = False
