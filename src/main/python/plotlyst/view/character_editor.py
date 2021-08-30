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

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from fbs_runtime import platform

from src.main.python.plotlyst.core.domain import Novel, Character, BackstoryEvent
from src.main.python.plotlyst.view.common import emoji_font, spacer_widget
from src.main.python.plotlyst.view.dialog.character import BackstoryEditorDialog
from src.main.python.plotlyst.view.dialog.template import customize_character_profile
from src.main.python.plotlyst.view.generated.character_editor_ui import Ui_CharacterEditor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterBackstoryCard
from src.main.python.plotlyst.view.widget.template import ProfileTemplateView
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
        self.ui.btnNewBackstory.clicked.connect(self._new_backstory)

        self.profile = ProfileTemplateView(self.character, self.novel.character_profiles[0])
        self._init_profile_view()

        for backstory in self.character.backstory:
            card = CharacterBackstoryCard(backstory)
            card.deleteRequested.connect(self._remove_backstory)
            self.ui.wdgBackstory.layout().addWidget(card)

        self.ui.btnClose.setIcon(IconRegistry.return_icon())
        self.ui.btnClose.clicked.connect(self._save)

        self.repo = RepositoryPersistenceManager.instance()

    def _init_profile_view(self):
        self._profile_with_toolbar = QWidget()
        self._toolbar = QWidget()
        self._toolbar.setLayout(QHBoxLayout())
        self._toolbar.layout().setContentsMargins(0, 0, 0, 0)
        self._toolbar.layout().addWidget(spacer_widget())
        self._toolbar.layout().addWidget(self.ui.btnCustomize)
        self._profile_with_toolbar.setLayout(QVBoxLayout())
        self._profile_with_toolbar.layout().setContentsMargins(0, 0, 0, 0)
        self._profile_with_toolbar.layout().addWidget(self._toolbar)
        self._profile_with_toolbar.layout().addWidget(self.profile)
        self._profile_container = QWidget()
        self._profile_container.setLayout(QHBoxLayout())
        self._profile_container.layout().setContentsMargins(0, 0, 0, 0)
        self._profile_container.layout().addWidget(self._profile_with_toolbar)
        self.ui.wdgProfile.layout().insertWidget(0, self._profile_container)

    def _customize_profile(self):
        profile_index = 0
        updated = customize_character_profile(self.novel, profile_index, self.widget)
        if not updated:
            return
        self.profile = ProfileTemplateView(self.character, self.novel.character_profiles[profile_index])

        self.ui.wdgProfile.layout().takeAt(0)
        self._profile_container.deleteLater()
        self._init_profile_view()

    def _new_backstory(self):
        backstory: Optional[BackstoryEvent] = BackstoryEditorDialog().display()
        if backstory:
            card = CharacterBackstoryCard(backstory)
            card.deleteRequested.connect(self._remove_backstory)
            self.ui.wdgBackstory.layout().addWidget(card)
            self.character.backstory.append(backstory)

    def _remove_backstory(self, card: CharacterBackstoryCard):
        if card.backstory in self.character.backstory:
            self.character.backstory.remove(card.backstory)

        self.ui.wdgBackstory.layout().removeWidget(card)

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

        self._new_character = False
