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
from functools import partial

import qtanim
from PyQt6.QtCore import pyqtSignal, QObject, QTimer
from PyQt6.QtWidgets import QWidget, QAbstractButton, QLineEdit, QCompleter
from overrides import overrides
from qthandy import translucent, btn_popup, bold, italic, margins
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from plotlyst.common import PLOTLYST_SECONDARY_COLOR
from plotlyst.core.client import json_client
from plotlyst.core.domain import Novel, Character, Document, MALE, FEMALE, SelectionItem
from plotlyst.core.template import protagonist_role
from plotlyst.event.core import EventListener, Event
from plotlyst.event.handler import event_dispatchers, global_event_dispatcher
from plotlyst.events import NovelAboutToSyncEvent
from plotlyst.resources import resource_registry
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.service.tour import TourService
from plotlyst.view.common import emoji_font, set_tab_icon, wrap, ButtonPressResizeEventFilter
from plotlyst.view.dialog.template import customize_character_profile
from plotlyst.view.generated.character_editor_ui import Ui_CharacterEditor
from plotlyst.view.icons import IconRegistry
from plotlyst.view.style.base import apply_bg_image, apply_white_menu
from plotlyst.view.widget.big_five import BigFivePersonalityWidget
from plotlyst.view.widget.character.editor import CharacterAgeEditor
from plotlyst.view.widget.character.editor import CharacterRoleSelector
from plotlyst.view.widget.character.plan import CharacterPlansWidget
from plotlyst.view.widget.character.topic import CharacterTopicsEditor
from plotlyst.view.widget.template import CharacterProfileTemplateView
from plotlyst.view.widget.tour.core import CharacterEditorTourEvent, \
    CharacterEditorNameLineEditTourEvent, TourEvent, CharacterEditorNameFilledTourEvent, \
    CharacterEditorAvatarDisplayTourEvent, CharacterEditorAvatarMenuTourEvent, CharacterEditorBackButtonTourEvent, \
    CharacterEditorAvatarMenuCloseTourEvent


class CharacterEditor(QObject, EventListener):
    close = pyqtSignal()

    def __init__(self, novel: Novel, character: Character = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_CharacterEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel
        self.character = character

        self._emoji_font = emoji_font()
        self.ui.btnNewBackstory.setIcon(IconRegistry.plus_icon('white'))
        self.ui.btnNewBackstory.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnNewBackstory))
        self.ui.btnNewBackstory.clicked.connect(lambda: self.ui.wdgBackstory.add())
        self.ui.tabAttributes.currentChanged.connect(self._tab_changed)
        self.ui.textEdit.setTitleVisible(False)
        self.ui.textEdit.setWidthPercentage(95)

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
        self.ui.btnMoreGender.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnMoreGender))
        self.ui.btnMoreGender.clicked.connect(self._display_more_gender_clicked)

        self.ui.btnRole.setIcon(IconRegistry.from_name('fa5s.chess-bishop'))
        self._btnRoleEventFilter = OpacityEventFilter(parent=self.ui.btnRole, leaveOpacity=0.7,
                                                      ignoreCheckedButton=True)
        self.ui.btnRole.installEventFilter(self._btnRoleEventFilter)
        self._roleSelector = CharacterRoleSelector()
        self._roleSelector.roleSelected.connect(self._role_changed)
        self._roleSelector.rolePromoted.connect(self._role_promoted)
        if self.character.role:
            self._roleSelector.setActiveRole(self.character.role)
        self._roleMenu = MenuWidget(self.ui.btnRole)
        self._roleMenu.addWidget(self._roleSelector)

        italic(self.ui.btnAge)
        italic(self.ui.btnOccupation)

        self._ageEditor = CharacterAgeEditor()
        self._ageEditor.valueChanged.connect(self._age_changed)
        self._ageEditor.infiniteToggled.connect(self._age_infinite_toggled)
        menu = MenuWidget(self.ui.btnAge)
        menu.addWidget(self._ageEditor)
        apply_white_menu(menu)
        menu.aboutToShow.connect(self._ageEditor.setFocus)

        self._lineOccupation = QLineEdit()
        self._lineOccupation.setPlaceholderText('Fill out occupation')
        self._lineOccupation.textChanged.connect(self._occupation_changed)
        occupations = set([x.occupation for x in self.novel.characters])
        if occupations:
            self._lineOccupation.setCompleter(QCompleter(occupations))
        menu = btn_popup(self.ui.btnOccupation, wrap(self._lineOccupation, margin_bottom=2))
        menu.aboutToShow.connect(self._lineOccupation.setFocus)
        self._lineOccupation.editingFinished.connect(menu.hide)

        # incr_font(self.ui.btnAge, 2)
        # incr_font(self.ui.btnOccupation, 2)

        if self.character.age:
            self._ageEditor.setValue(self.character.age)
        self._ageEditor.setInfinite(self.character.age_infinite)
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

        set_tab_icon(self.ui.tabAttributes, self.ui.tabBackstory,
                     IconRegistry.backstory_icon('black', PLOTLYST_SECONDARY_COLOR))
        set_tab_icon(self.ui.tabAttributes, self.ui.tabTopics,
                     IconRegistry.topics_icon(color_on=PLOTLYST_SECONDARY_COLOR))
        set_tab_icon(self.ui.tabAttributes, self.ui.tabBigFive, IconRegistry.big_five_icon(PLOTLYST_SECONDARY_COLOR))
        set_tab_icon(self.ui.tabAttributes, self.ui.tabNotes, IconRegistry.document_edition_icon())
        set_tab_icon(self.ui.tabAttributes, self.ui.tabGoals, IconRegistry.goal_icon('black', PLOTLYST_SECONDARY_COLOR))

        self._bigFive = BigFivePersonalityWidget()
        self._bigFive.setCharacter(self.character)
        self.ui.tabBigFive.layout().addWidget(self._bigFive)

        self.ui.wdgAvatar.btnAvatar.setToolTip('Character avatar. Click to add an image')
        self.ui.wdgAvatar.setCharacter(self.character)
        self.ui.wdgAvatar.setUploadPopupMenu()
        self.ui.wdgAvatar.avatarUpdated.connect(self.ui.wdgBackstory.refreshCharacter)
        self.ui.wdgAvatar.setFixedSize(180, 180)

        self.ui.splitter.setSizes([400, 400])

        self.ui.lineName.setReadOnly(self.novel.is_readonly())
        self.ui.lineName.textEdited.connect(self._name_edited)
        self.ui.lineName.setText(self.character.name)

        self._character_goals = CharacterPlansWidget(self.novel, self.character)
        self.ui.scrollAreaPlans.layout().addWidget(self._character_goals)
        margins(self.ui.tabGoals.layout(), left=5)

        self.wdgTopicsEditor = CharacterTopicsEditor()
        self.wdgTopicsEditor.setCharacter(self.character)
        self.ui.tabTopics.layout().addWidget(self.wdgTopicsEditor)

        self.profile = CharacterProfileTemplateView(self.character, self.novel.character_profiles[0])
        self.ui.wdgProfile.layout().addWidget(self.profile)

        self.ui.wdgBackstory.setCharacter(self.character)
        apply_bg_image(self.ui.scrollAreaBackstoryContents, resource_registry.cover1)

        if self.character.document and self.character.document.loaded:
            self.ui.textEdit.setText(self.character.document.content, self.character.name, title_read_only=True)

        self.ui.btnClose.clicked.connect(self._save)

        if self.character.role:
            self._display_role()

        self.ui.tabAttributes.setCurrentWidget(self.ui.tabTopics)

        self.repo = RepositoryPersistenceManager.instance()
        dispatcher = event_dispatchers.instance(self.novel)
        dispatcher.register(self, NovelAboutToSyncEvent)

        self._tour_service = TourService.instance()
        global_event_dispatcher.register(self, CharacterEditorTourEvent, CharacterEditorNameLineEditTourEvent,
                                         CharacterEditorNameFilledTourEvent, CharacterEditorAvatarDisplayTourEvent,
                                         CharacterEditorAvatarMenuTourEvent, CharacterEditorAvatarMenuCloseTourEvent,
                                         CharacterEditorBackButtonTourEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, TourEvent):
            self.__handle_tour_event(event)
        elif isinstance(event, NovelAboutToSyncEvent):
            self._save()

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

    def _role_promoted(self, role: SelectionItem):
        if self.character.role == role:
            self._display_role()
            if self.character.prefs.avatar.use_role:
                self.ui.wdgAvatar.updateAvatar()

    def _role_changed(self, role: SelectionItem):
        self._roleMenu.close()
        if role.text == protagonist_role.text and self.character.gender == FEMALE:
            role.icon = 'fa5s.chess-queen'
        self.character.role = role
        self._display_role()
        if self.character.prefs.avatar.use_role:
            self.ui.wdgAvatar.updateAvatar()

    def _age_changed(self, age: int):
        if self._ageEditor.minimum() == 0:
            italic(self.ui.btnAge, False)
            bold(self.ui.btnAge)
            self.ui.btnAge.iconColor = '#343a40'
        self.ui.btnAge.setText(str(age))
        self.character.age = age

    def _age_infinite_toggled(self, toggled: bool):
        if toggled:
            self.ui.btnAge.setIcon(IconRegistry.from_name('mdi.infinity', 'gray'))
            self.ui.btnAge.setText('')
        else:
            self.ui.btnAge.setIcon(IconRegistry.from_name('fa5s.birthday-cake', 'gray'))
            if self.character.age is not None:
                self.ui.btnAge.setText(str(self.character.age))

        self.character.age_infinite = toggled

    def _occupation_changed(self, occupation: str):
        if self.ui.btnOccupation.font().italic():  # first setup
            italic(self.ui.btnOccupation, False)
            bold(self.ui.btnOccupation)
            self.ui.btnOccupation.iconColor = '#343a40'
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
                anim.finished.connect(partial(translucent, other_btn, 0.4))

        if len(self.ui.btnGroupGender.buttons()) == 2:
            self.ui.btnMoreGender.setHidden(btn.isChecked())

    def _display_more_gender_clicked(self):
        for btn in [self.ui.btnTransgender, self.ui.btnNonBinary, self.ui.btnGenderless]:
            self.ui.btnGroupGender.addButton(btn)
            anim = qtanim.fade_in(btn)
            anim.finished.connect(partial(translucent, btn, 0.4))

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

        self.repo.update_character(self.character, self.ui.wdgAvatar.imageUploaded())
        self.repo.update_novel(self.novel)  # TODO temporary to update custom labels

        if not self.character.document:
            self.character.document = Document('', character_id=self.character.id)
            self.character.document.loaded = True

        if self.character.document.loaded:
            self.character.document.content = self.ui.textEdit.textEdit.toHtml()
            self.repo.update_doc(self.novel, self.character.document)

        self.close.emit()

    def __handle_tour_event(self, event: TourEvent):
        if isinstance(event, CharacterEditorTourEvent):
            self._tour_service.addWidget(self.widget, event)
        elif isinstance(event, CharacterEditorNameLineEditTourEvent):
            self._tour_service.addWidget(self.ui.lineName, event)
        elif isinstance(event, CharacterEditorNameFilledTourEvent):
            self.ui.lineName.setText(event.name)
            self._name_edited(event.name)
            self.ui.wdgAvatar.updateAvatar()
            self._tour_service.next()
        elif isinstance(event, CharacterEditorAvatarDisplayTourEvent):
            self._tour_service.addWidget(self.ui.wdgAvatar, event)
        elif isinstance(event, CharacterEditorAvatarMenuTourEvent):
            self.ui.wdgAvatar.popupMenu().exec()
            QTimer.singleShot(150, lambda: self._tour_service.addWidget(self.ui.wdgAvatar.popupMenu(), event))
        elif isinstance(event, CharacterEditorAvatarMenuCloseTourEvent):
            self.ui.wdgAvatar.popupMenu().close()
            self._tour_service.next()
        elif isinstance(event, CharacterEditorBackButtonTourEvent):
            self._tour_service.addWidget(self.ui.btnClose, event)
