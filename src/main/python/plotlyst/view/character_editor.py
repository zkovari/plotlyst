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
from functools import partial

import qtanim
from PyQt5.QtWidgets import QWidget, QAbstractButton, QSpinBox, QLineEdit
from fbs_runtime import platform
from qthandy import opaque, btn_popup, incr_font, bold, italic

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Character, Document, MALE, FEMALE, SelectionItem
from src.main.python.plotlyst.core.template import protagonist_role
from src.main.python.plotlyst.resources import resource_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import emoji_font, OpacityEventFilter
from src.main.python.plotlyst.view.dialog.template import customize_character_profile
from src.main.python.plotlyst.view.generated.character_editor_ui import Ui_CharacterEditor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterGoalsEditor, CharacterRoleSelector
from src.main.python.plotlyst.view.widget.template import CharacterProfileTemplateView


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
        self.ui.btnNewBackstory.clicked.connect(lambda: self.ui.wdgBackstory.add())
        self.ui.tabAttributes.currentChanged.connect(self._tab_changed)
        self.ui.textEdit.setTitleVisible(False)

        self.ui.btnMale.setIcon(IconRegistry.male_gender_icon())
        self.ui.btnMale.installEventFilter(OpacityEventFilter(parent=self.ui.btnMale, ignoreCheckedButton=True))
        self.ui.btnFemale.setIcon(IconRegistry.female_gender_icon())
        self.ui.btnFemale.installEventFilter(OpacityEventFilter(parent=self.ui.btnFemale, ignoreCheckedButton=True))
        self.ui.btnTransgender.setIcon(IconRegistry.transgender_icon())
        self.ui.btnTransgender.installEventFilter(
            OpacityEventFilter(parent=self.ui.btnTransgender, ignoreCheckedButton=True))
        self.ui.btnTransgender.setHidden(True)
        self.ui.btnNonBinary.setIcon(IconRegistry.non_binary_gender_icon())
        self.ui.btnNonBinary.installEventFilter(
            OpacityEventFilter(parent=self.ui.btnNonBinary, ignoreCheckedButton=True))
        self.ui.btnNonBinary.setHidden(True)
        self.ui.btnGenderless.setIcon(IconRegistry.genderless_icon())
        self.ui.btnGenderless.installEventFilter(
            OpacityEventFilter(parent=self.ui.btnGenderless, ignoreCheckedButton=True))
        self.ui.btnGenderless.setHidden(True)
        self.ui.btnGroupGender.buttonClicked.connect(self._gender_clicked)
        self.ui.btnMoreGender.clicked.connect(self._display_more_gender_clicked)

        self.ui.btnRole.setIcon(IconRegistry.from_name('fa5s.chess-bishop'))
        self._btnRoleEventFilter = OpacityEventFilter(leaveOpacity=0.7, parent=self.ui.btnRole,
                                                      ignoreCheckedButton=True)
        self.ui.btnRole.installEventFilter(self._btnRoleEventFilter)
        self._roleSelector = CharacterRoleSelector()
        self._roleSelector.roleSelected.connect(self._role_changed)
        btn_popup(self.ui.btnRole, self._roleSelector)

        self._sbAge = QSpinBox()
        self._sbAge.setMinimum(0)
        self._sbAge.setMaximum(65000)
        self._sbAge.valueChanged.connect(self._age_changed)
        menu = btn_popup(self.ui.btnAge, self._sbAge)
        menu.aboutToShow.connect(self._sbAge.setFocus)
        self._sbAge.editingFinished.connect(menu.hide)

        self._lineOccupation = QLineEdit()
        self._lineOccupation.setPlaceholderText('Fill out occupation')
        self._lineOccupation.textChanged.connect(self._occupation_changed)
        menu = btn_popup(self.ui.btnOccupation, self._lineOccupation)
        menu.aboutToShow.connect(self._lineOccupation.setFocus)
        self._lineOccupation.editingFinished.connect(menu.hide)

        if self.character.age:
            self._sbAge.setValue(self.character.age)
        if self.character.occupation:
            self._lineOccupation.setText(self.character.occupation)

        if self.character.gender:
            self.ui.btnMoreGender.setHidden(True)
            if self.character.gender == MALE:
                self.ui.btnMale.setChecked(True)
            elif self.character.gender == FEMALE:
                self.ui.btnFemale.setChecked(True)
            else:
                for btn in [self.ui.btnTransgender, self.ui.btnNonBinary, self.ui.btnGenderless]:
                    self.ui.btnGroupGender.addButton(btn)
                    if self.character.gender == btn.text():
                        btn.setChecked(True)
                        btn.setVisible(True)

            for btn in self.ui.btnGroupGender.buttons():
                if not btn.isChecked():
                    btn.setHidden(True)

        self.ui.wdgAvatar.btnPov.setToolTip('Character avatar. Click to add an image')
        self.ui.wdgAvatar.setCharacter(self.character)
        self.ui.wdgAvatar.setUploadPopupMenu()

        self.ui.splitter.setSizes([400, 400])

        self.ui.lineName.textEdited.connect(self._name_edited)
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

        if self.character.role:
            self._display_role()

        self.repo = RepositoryPersistenceManager.instance()

    def _customize_profile(self):
        profile_index = 0
        updated = customize_character_profile(self.novel, profile_index, self.widget)
        if not updated:
            return
        self.profile = CharacterProfileTemplateView(self.character, self.novel.character_profiles[profile_index])

    def _name_edited(self, text: str):
        self.character.name = text
        if self.character.prefs.avatar.use_initial:
            self.ui.wdgAvatar.updateAvatar()

    def _tab_changed(self, index: int):
        if self.ui.tabAttributes.widget(index) is self.ui.tabNotes:
            if self.character.document and not self.character.document.loaded:
                json_client.load_document(self.novel, self.character.document)
                self.ui.textEdit.setText(self.character.document.content, self.character.name, title_read_only=True)

    def _role_changed(self, role: SelectionItem):
        self.ui.btnRole.menu().hide()
        if role.text == protagonist_role.text and self.character.gender == FEMALE:
            role.icon = 'fa5s.chess-queen'
        self.character.role = role
        self._display_role()
        if self.character.prefs.avatar.use_role:
            self.ui.wdgAvatar.updateAvatar()

    def _age_changed(self, age: int):
        if self._sbAge.minimum() == 0:
            self._sbAge.setMinimum(1)
            incr_font(self.ui.btnAge, 2)
            italic(self.ui.btnAge, False)
            bold(self.ui.btnAge)
            self.ui.btnAge.iconColor = '#343a40'
            self.ui.btnAge.setStyleSheet('''
                        QPushButton::menu-indicator {width:0px;}
                        QPushButton {
                            border: 1px hidden black;
                            border-radius: 6px;
                            color: #343a40;
                            padding: 2px;
                        }
                    ''')
        self.ui.btnAge.setText(str(age))
        self.character.age = age

    def _occupation_changed(self, occupation: str):
        if self.ui.btnOccupation.font().italic():  # first setup
            italic(self.ui.btnOccupation, False)
            bold(self.ui.btnOccupation)
            incr_font(self.ui.btnOccupation, 2)
            self.ui.btnOccupation.iconColor = '#343a40'
            self.ui.btnOccupation.setStyleSheet('''
                                    QPushButton::menu-indicator {width:0px;}
                                    QPushButton {
                                        border: 1px hidden black;
                                        border-radius: 6px;
                                        color: #343a40;
                                        padding: 2px;
                                    }
                                ''')
        self.ui.btnOccupation.setText(occupation)
        self.character.occupation = occupation

    def _display_role(self):
        self.ui.btnRole.setText(self.character.role.text)
        if self.character.role.icon:
            self.ui.btnRole.setIcon(IconRegistry.from_name(self.character.role.icon, self.character.role.icon_color))
        self.ui.btnRole.setStyleSheet(f'''
            #btnRole {{
                border: 2px solid {self.character.role.icon_color};
                color: {self.character.role.icon_color};
                border-radius: 6px;
                padding: 3px;
                font: bold;
            }}
            #btnRole::menu-indicator {{width:0px;}}
            #btnRole:pressed {{
                border: 2px solid white;
            }}
        ''')
        self._btnRoleEventFilter.enterOpacity = 0.8

        if self.character.is_minor():
            self.profile.toggleRequiredHeaders(True)
        else:
            self.profile.toggleRequiredHeaders(False)

    def _gender_clicked(self, btn: QAbstractButton):
        self.ui.btnMoreGender.setHidden(True)

        for other_btn in self.ui.btnGroupGender.buttons():
            if other_btn is btn:
                continue

            if btn.isChecked():
                other_btn.setChecked(False)
                qtanim.fade_out(other_btn)
            else:
                anim = qtanim.fade_in(other_btn)
                anim.finished.connect(partial(opaque, other_btn, 0.4))

        if len(self.ui.btnGroupGender.buttons()) == 2:
            self.ui.btnMoreGender.setHidden(btn.isChecked())

    def _display_more_gender_clicked(self):
        for btn in [self.ui.btnTransgender, self.ui.btnNonBinary, self.ui.btnGenderless]:
            self.ui.btnGroupGender.addButton(btn)
            anim = qtanim.fade_in(btn)
            anim.finished.connect(partial(opaque, btn, 0.4))

        self.ui.btnMoreGender.setHidden(True)

    def _save(self):
        gender = ''
        for btn in self.ui.btnGroupGender.buttons():
            if btn.isChecked():
                gender = btn.text()
                break
        self.character.gender = gender
        if self.character.role and self.character.role.text == protagonist_role.text:
            if self.character.gender == FEMALE:
                self.character.role.icon = 'fa5s.chess-queen'
            else:
                self.character.role.icon = 'fa5s.chess-king'
        self.character.name = self.ui.lineName.text()
        self.character.template_values = self.profile.values()

        self.repo.update_character(self.character, self.ui.wdgAvatar.avatarUpdated())
        self.repo.update_novel(self.novel)  # TODO temporary to update custom labels

        if not self.character.document:
            self.character.document = Document('', character_id=self.character.id)
            self.character.document.loaded = True

        if self.character.document.loaded:
            self.character.document.content = self.ui.textEdit.textEdit.toHtml()
            self.repo.update_doc(self.novel, self.character.document)
