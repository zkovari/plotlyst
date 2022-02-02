"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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

from PyQt5.QtWidgets import QWidget
from fbs_runtime import platform

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Character, Document
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view.common import emoji_font, spacer_widget
from src.main.python.plotlyst.view.dialog.template import customize_character_profile
from src.main.python.plotlyst.view.generated.character_editor_ui import Ui_CharacterEditor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import hbox, vbox
from src.main.python.plotlyst.view.widget.template import CharacterProfileTemplateView
from src.main.python.plotlyst.worker.persistence import RepositoryPersistenceManager


class CharacterEditor:

    def __init__(self, novel: Novel, character: Optional[Character] = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_CharacterEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel

        if character:
            self.character = character
            self._new_character = False
        else:
            self.character = Character('')
            self._new_character = True

        if platform.is_windows():
            self._emoji_font = emoji_font(14)
        else:
            self._emoji_font = emoji_font(20)
        self.ui.btnCustomize.setIcon(IconRegistry.customization_icon())
        self.ui.btnCustomize.clicked.connect(self._customize_profile)
        self.ui.btnNewBackstory.setIcon(IconRegistry.plus_icon())
        self.ui.btnNewBackstory.clicked.connect(self.ui.wdgBackstory.add)
        self.ui.tabAttributes.currentChanged.connect(self._tab_changed)
        self.ui.textEdit.setTitleVisible(False)

        self.ui.wdgJournal.setCharacter(self.novel, self.character)

        self.profile = CharacterProfileTemplateView(self.character, self.novel.character_profiles[0])
        self._init_profile_view()

        self.ui.wdgBackstory.setCharacter(self.character)
        self.widget.setStyleSheet(
            f'''#scrollAreaWidgetContents {{background-image: url({resource_registry.cover1});}}
                               ''')

        if self.character.document and self.character.document.loaded:
            self.ui.textEdit.setText(self.character.document.content, self.character.name, title_read_only=True)

        self.ui.btnClose.setIcon(IconRegistry.return_icon())
        self.ui.btnClose.clicked.connect(self._save)

        self.repo = RepositoryPersistenceManager.instance()

    def _init_profile_view(self):
        self._profile_with_toolbar = QWidget()
        self._toolbar = QWidget()
        hbox(self._toolbar, 0)
        self._toolbar.layout().addWidget(spacer_widget())
        self._toolbar.layout().addWidget(self.ui.btnCustomize)
        vbox(self._profile_with_toolbar, 0)
        self._profile_with_toolbar.layout().addWidget(self._toolbar)
        self._profile_with_toolbar.layout().addWidget(self.profile)
        self._profile_container = QWidget()
        hbox(self._profile_container, 0)
        self._profile_container.layout().addWidget(self._profile_with_toolbar)
        self.ui.wdgProfile.layout().insertWidget(0, self._profile_container)

    def _customize_profile(self):
        profile_index = 0
        updated = customize_character_profile(self.novel, profile_index, self.widget)
        if not updated:
            return
        self.profile = CharacterProfileTemplateView(self.character, self.novel.character_profiles[profile_index])

        self.ui.wdgProfile.layout().takeAt(0)
        self._profile_container.deleteLater()
        self._init_profile_view()

    def _tab_changed(self, index: int):
        if self.ui.tabAttributes.widget(index) is self.ui.tabNotes:
            if self.character.document and not self.character.document.loaded:
                json_client.load_document(self.novel, self.character.document)
                self.ui.textEdit.setText(self.character.document.content, self.character.name, title_read_only=True)

    def _save(self):
        name = self.profile.name()
        if not name:
            return
        self.character.name = name
        self.character.template_values = self.profile.values()

        if self._new_character:
            self.novel.characters.append(self.character)
            self.repo.insert_character(self.novel, self.character)
        else:
            self.repo.update_character(self.character, self.profile.avatarUpdated())
            self.repo.update_novel(self.novel)  # TODO temporary to update custom labels

        if not self.character.document:
            self.character.document = Document('', character_id=self.character.id)
            self.character.document.loaded = True

        if self.character.document.loaded:
            self.character.document.content = self.ui.textEdit.textEditor.toHtml()
            self.repo.update_doc(self.novel, self.character.document)

        self._new_character = False
