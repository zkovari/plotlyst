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

import qtanim
from PyQt5.QtWidgets import QWidget
from fbs_runtime import platform

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Character, Document
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.view.common import emoji_font, OpacityEventFilter
from src.main.python.plotlyst.view.dialog.template import customize_character_profile
from src.main.python.plotlyst.view.generated.character_editor_ui import Ui_CharacterEditor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterGoalsEditor
from src.main.python.plotlyst.view.widget.template import CharacterProfileTemplateView
from src.main.python.plotlyst.worker.persistence import RepositoryPersistenceManager


class CharacterEditor:

    def __init__(self, novel: Novel, character: Character = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_CharacterEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel
        self.character = character

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

        self.ui.btnMale.setIcon(IconRegistry.from_name('mdi.gender-male', color_on='#067bc2'))
        self.ui.btnFemale.setIcon(IconRegistry.from_name('mdi.gender-female', color_on='#832161'))
        self.ui.btnMale.installEventFilter(OpacityEventFilter(parent=self.ui.btnMale, ignoreCheckedButton=True))
        self.ui.btnFemale.installEventFilter(OpacityEventFilter(parent=self.ui.btnFemale, ignoreCheckedButton=True))
        self.ui.btnMale.clicked.connect(self._male_clicked)
        self.ui.btnFemale.clicked.connect(self._female_clicked)

        self.ui.lineName.setText(self.character.name)

        self._character_goals = CharacterGoalsEditor(self.novel, self.character)
        self.ui.tabGoals.layout().addWidget(self._character_goals)

        self.profile = CharacterProfileTemplateView(self.character, self.novel.character_profiles[0])
        self.ui.wdgProfile.layout().addWidget(self.profile)

        self.ui.wdgBackstory.setCharacter(self.character)
        self.widget.setStyleSheet(
            f'''#scrollAreaWidgetContents {{background-image: url({resource_registry.cover1});}}
                               ''')

        if self.character.document and self.character.document.loaded:
            self.ui.textEdit.setText(self.character.document.content, self.character.name, title_read_only=True)

        self.ui.btnClose.setIcon(IconRegistry.return_icon())
        self.ui.btnClose.clicked.connect(self._save)

        self.repo = RepositoryPersistenceManager.instance()

    def _customize_profile(self):
        profile_index = 0
        updated = customize_character_profile(self.novel, profile_index, self.widget)
        if not updated:
            return
        self.profile = CharacterProfileTemplateView(self.character, self.novel.character_profiles[profile_index])

    def _tab_changed(self, index: int):
        if self.ui.tabAttributes.widget(index) is self.ui.tabNotes:
            if self.character.document and not self.character.document.loaded:
                json_client.load_document(self.novel, self.character.document)
                self.ui.textEdit.setText(self.character.document.content, self.character.name, title_read_only=True)

    def _male_clicked(self, checked: bool):
        if checked:
            self.ui.btnFemale.setChecked(False)
            qtanim.fade_out(self.ui.btnFemale)
        else:
            self.ui.btnFemale.setVisible(True)
            qtanim.fade_in(self.ui.btnFemale)

    def _female_clicked(self, checked: bool):
        if checked:
            self.ui.btnMale.setChecked(False)
            qtanim.fade_out(self.ui.btnMale)
        else:
            self.ui.btnMale.setVisible(True)
            qtanim.fade_in(self.ui.btnMale)

    def _save(self):
        self.character.name = self.ui.lineName.text()
        self.character.template_values = self.profile.values()

        self.repo.update_character(self.character, self.profile.avatarUpdated())
        self.repo.update_novel(self.novel)  # TODO temporary to update custom labels

        if not self.character.document:
            self.character.document = Document('', character_id=self.character.id)
            self.character.document.loaded = True

        if self.character.document.loaded:
            self.character.document.content = self.ui.textEdit.textEdit.toHtml()
            self.repo.update_doc(self.novel, self.character.document)
