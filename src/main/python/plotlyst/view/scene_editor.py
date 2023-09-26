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
from typing import Optional

import emoji
import qtanim
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QTableView
from overrides import overrides
from qtanim import fade_in
from qthandy import underline, incr_font, margins
from qtmenu import MenuWidget, ScrollableMenuWidget

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Scene, Document, StoryBeat, \
    Character, TagReference, ScenePurposeType, ScenePurpose
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_info, EventListener, Event, emit_event
from src.main.python.plotlyst.event.handler import event_dispatchers
from src.main.python.plotlyst.events import NovelAboutToSyncEvent, SceneStoryBeatChangedEvent
from src.main.python.plotlyst.model.characters_model import CharactersSceneAssociationTableModel
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import emoji_font, ButtonPressResizeEventFilter, action, set_tab_icon
from src.main.python.plotlyst.view.generated.scene_editor_ui import Ui_SceneEditor
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.labels import CharacterLabel
from src.main.python.plotlyst.view.widget.scene.editor import ScenePurposeSelectorWidget, ScenePurposeTypeButton, \
    SceneStorylineEditor, SceneAgendaEditor
from src.main.python.plotlyst.view.widget.scenes import SceneTagSelector


class SceneEditor(QObject, EventListener):
    close = pyqtSignal()

    def __init__(self, novel: Novel, scene: Optional[Scene] = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_SceneEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel
        self.scene: Optional[Scene] = None
        self.notes_updated: bool = False

        self._emoji_font = emoji_font()

        # self.ui.btnDrive.setIcon(IconRegistry.from_name('mdi.chemical-weapon'))
        set_tab_icon(self.ui.tabWidget, self.ui.tabStorylines, IconRegistry.story_structure_icon())
        set_tab_icon(self.ui.tabWidget, self.ui.tabCharacter, IconRegistry.character_icon())
        set_tab_icon(self.ui.tabWidget, self.ui.tabStructure,
                     IconRegistry.from_name('mdi6.timeline-outline', rotated=90))
        set_tab_icon(self.ui.tabWidget, self.ui.tabNotes, IconRegistry.document_edition_icon())

        self.ui.btnStageCharacterLabel.setIcon(IconRegistry.character_icon(color_on='black'))
        underline(self.ui.btnStageCharacterLabel)

        if app_env.is_mac():
            incr_font(self.ui.lineTitle)
            incr_font(self.ui.textSynopsis)
        self.ui.lineTitle.setReadOnly(self.novel.is_readonly())
        self.ui.lineTitle.textEdited.connect(self._title_edited)

        # self.ui.lblDayEmoji.setFont(self._emoji_font)
        # self.ui.lblDayEmoji.setText(emoji.emojize(':spiral_calendar:'))
        self.ui.lblDayEmoji.setHidden(True)
        self.ui.sbDay.setHidden(True)
        self.ui.lblTitleEmoji.setFont(self._emoji_font)
        self.ui.lblTitleEmoji.setText(emoji.emojize(':clapper_board:'))
        self.ui.lblSynopsisEmoji.setFont(self._emoji_font)
        self.ui.lblSynopsisEmoji.setText(emoji.emojize(':scroll:'))

        self.ui.wdgStructure.setBeatsCheckable(True)
        self.ui.wdgStructure.setStructure(self.novel)
        self.ui.wdgStructure.setActsClickable(False)
        self.ui.wdgStructure.beatSelected.connect(self._beat_selected)
        self.ui.wdgStructure.setRemovalContextMenuEnabled(True)
        self.ui.wdgStructure.beatRemovalRequested.connect(self._beat_removed)

        self._povMenu = ScrollableMenuWidget(self.ui.wdgPov.btnAvatar)
        for char in self.novel.characters:
            self._povMenu.addAction(action(char.name, avatars.avatar(char), partial(self._on_pov_changed, char)))
        self.ui.wdgPov.btnAvatar.setText('POV')
        self.ui.wdgPov.setFixedSize(170, 170)

        self.ui.textNotes.setTitleVisible(False)
        self.ui.textNotes.setPlaceholderText("Scene notes")

        self.tblCharacters = QTableView()
        self.tblCharacters.setShowGrid(False)
        self.tblCharacters.verticalHeader().setVisible(False)
        self.tblCharacters.horizontalHeader().setVisible(False)
        self.tblCharacters.horizontalHeader().setDefaultSectionSize(200)
        self.tblCharacters.setCursor(Qt.CursorShape.PointingHandCursor)

        self._characters_model = CharactersSceneAssociationTableModel(self.novel)
        self._characters_model.selection_changed.connect(self._character_changed)
        self.tblCharacters.setModel(self._characters_model)
        self.tblCharacters.clicked.connect(self._characters_model.toggleSelection)

        self.ui.btnEditCharacters.setIcon(IconRegistry.plus_edit_icon())
        menu = MenuWidget(self.ui.btnEditCharacters)
        menu.addWidget(self.tblCharacters)
        self.ui.btnEditCharacters.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnEditCharacters))
        self.ui.btnStageCharacterLabel.clicked.connect(lambda: menu.exec())

        self.tag_selector = SceneTagSelector(self.novel, self.scene)
        self.ui.wdgTags.layout().addWidget(self.tag_selector)

        self.ui.treeScenes.setNovel(self.novel, readOnly=True)
        self.ui.treeScenes.sceneSelected.connect(self._scene_selected)

        self._purposeSelector = ScenePurposeSelectorWidget()
        margins(self._purposeSelector, top=25)
        self.ui.pagePurpose.layout().addWidget(self._purposeSelector)
        self._purposeSelector.skipped.connect(self._purposeSkipped)
        self._purposeSelector.selected.connect(self._purposeChanged)

        self._btnPurposeType = ScenePurposeTypeButton(ScenePurposeType.Other)
        self._btnPurposeType.selectionRequested.connect(self._resetPurposeEditor)
        self.ui.wdgMidbar.layout().insertWidget(0, self._btnPurposeType)

        self._storylineEditor = SceneStorylineEditor(self.novel)
        self.ui.tabStorylines.layout().addWidget(self._storylineEditor)

        self._agencyEditor = SceneAgendaEditor(self.novel)
        self.ui.tabCharacter.layout().addWidget(self._agencyEditor)

        self.ui.btnClose.clicked.connect(self._on_close)

        self.ui.wdgSceneStructure.setUnsetCharacterSlot(self._pov_not_selected_notification)

        self._update_view(scene)
        self.ui.tabWidget.setCurrentWidget(self.ui.tabStorylines)
        self.ui.tabWidget.currentChanged.connect(self._page_toggled)

        self.repo = RepositoryPersistenceManager.instance()

        dispatcher = event_dispatchers.instance(self.novel)
        dispatcher.register(self, NovelAboutToSyncEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, NovelAboutToSyncEvent):
            self._on_close()

    def _update_view(self, scene: Optional[Scene] = None):
        if scene:
            self.scene = scene
            self._new_scene = False
            self.ui.treeScenes.selectScene(self.scene)
        else:
            self.scene = self.novel.new_scene()
            if len(self.novel.scenes) > 1:
                self.scene.day = self.novel.scenes[-1].day
            self._new_scene = True

        if self.scene.pov:
            for agenda in self.scene.agendas:
                if not agenda.character_id:
                    agenda.character_id = self.scene.pov.id
        self._update_pov_avatar()
        self.ui.sbDay.setValue(self.scene.day)

        self.ui.wdgSceneStructure.setScene(self.novel, self.scene)
        self.tag_selector.setScene(self.scene)
        self._storylineEditor.setScene(self.scene)

        self.ui.lineTitle.setText(self.scene.title)
        self.ui.textSynopsis.setText(self.scene.synopsis)

        self.ui.wdgStructure.unhighlightBeats()
        if not self._new_scene:
            self.ui.wdgStructure.highlightScene(self.scene)
        self.ui.wdgStructure.uncheckActs()
        self.ui.wdgStructure.setActChecked(acts_registry.act(self.scene))

        self.notes_updated = False
        if self.ui.tabWidget.currentWidget() is self.ui.tabNotes or (
                self.scene.document and self.scene.document.loaded):
            self._update_notes()
        else:
            self.ui.textNotes.clear()

        if self.scene.purpose is None:
            self._resetPurposeEditor()
        else:
            self._closePurposeEditor()

        self._characters_model.setScene(self.scene)
        self._character_changed()

    def _page_toggled(self):
        if self.ui.tabWidget.currentWidget() is self.ui.tabNotes:
            self._update_notes()

    def _beat_selected(self, beat: StoryBeat):
        if self.scene.beat(self.novel) and self.scene.beat(self.novel) != beat:
            self.ui.wdgStructure.toggleBeat(self.scene.beat(self.novel), False)
            self.scene.remove_beat(self.novel)

        self.scene.link_beat(self.novel.active_story_structure, beat)
        self.ui.wdgStructure.highlightScene(self.scene)

        emit_event(self.novel, SceneStoryBeatChangedEvent(self, self.scene))

    def _beat_removed(self, beat: StoryBeat):
        scene = acts_registry.scene(beat)
        if scene is None:
            return

        scene.remove_beat(self.novel)
        self.ui.wdgStructure.unhighlightBeats()
        self.ui.wdgStructure.toggleBeat(beat, False)
        if self.scene == scene:
            self.ui.wdgStructure.highlightScene(self.scene)
        else:
            self.repo.update_scene(scene)

        emit_event(self.novel, SceneStoryBeatChangedEvent(self, scene))

    def _update_notes(self):
        if self.scene.document:
            if not self.scene.document.loaded:
                json_client.load_document(self.novel, self.scene.document)
            if not self.notes_updated:
                self.ui.textNotes.setText(self.scene.document.content, self.scene.title, title_read_only=True)
                self.notes_updated = True
        else:
            self.ui.textNotes.clear()

    def _pov_not_selected_notification(self):
        emit_info('POV character must be selected first')
        qtanim.shake(self.ui.wdgPov)

    def _on_pov_changed(self, pov: Character):
        self.scene.pov = pov

        self.scene.agendas[0].set_character(self.scene.pov)
        self.scene.agendas[0].conflict_references.clear()

        self._update_pov_avatar()
        self._characters_model.update()
        self._character_changed()
        # self.ui.wdgSceneStructure.updateAgendaCharacter()
        self.ui.treeScenes.refreshScene(self.scene)

    def _update_pov_avatar(self):
        if self.scene.pov:
            self.ui.wdgPov.setCharacter(self.scene.pov)
            self.ui.wdgPov.btnAvatar.setToolTip(f'<html>Point of view character: <b>{self.scene.pov.name}</b>')
        else:
            self.ui.wdgPov.reset()
            self.ui.wdgPov.btnAvatar.setToolTip('Select point of view character')

    def _title_edited(self, text: str):
        self.scene.title = text
        self.ui.treeScenes.refreshScene(self.scene)

    def _character_changed(self):
        self.ui.wdgCharacters.clear()

        for character in self.scene.characters:
            self.ui.wdgCharacters.addLabel(CharacterLabel(character))

        # self.ui.wdgSceneStructure.updateAvailableAgendaCharacters()

    def _purposeSkipped(self):
        self.scene.purpose = ScenePurposeType.Other
        self._closePurposeEditor()

    def _purposeChanged(self, purpose: ScenePurpose):
        self.scene.purpose = purpose.type
        if purpose.type == ScenePurposeType.Story:
            pass
        self._closePurposeEditor()

    def _closePurposeEditor(self):
        self._btnPurposeType.setPurposeType(self.scene.purpose)
        if not self._btnPurposeType.isVisible():
            fade_in(self._btnPurposeType)
        if not self.ui.btnInfo.isVisible():
            fade_in(self.ui.btnInfo)
        # to avoid segfault for some reason, we disable it first before changing the stack widget
        self._purposeSelector.setDisabled(True)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEditor)

    def _resetPurposeEditor(self):
        self.scene.purpose = None
        self._btnPurposeType.setHidden(True)
        self.ui.btnInfo.setHidden(True)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pagePurpose)
        self._purposeSelector.setEnabled(True)

    def _save_scene(self):
        self.scene.title = self.ui.lineTitle.text()
        self.scene.synopsis = self.ui.textSynopsis.toPlainText()
        self.scene.day = self.ui.sbDay.value()

        self.scene.tag_references.clear()
        for tag in self.tag_selector.tags():
            self.scene.tag_references.append(TagReference(tag.id))

        if self._new_scene:
            self.novel.scenes.append(self.scene)
            self.repo.insert_scene(self.novel, self.scene)
        else:
            self.repo.update_scene(self.scene)

        if not self.scene.document:
            self.scene.document = Document('', scene_id=self.scene.id)
            self.scene.document.loaded = True

        if self.scene.document.loaded:
            self.scene.document.content = self.ui.textNotes.textEdit.toHtml()
            self.repo.update_doc(self.novel, self.scene.document)
        self._new_scene = False

    def _on_close(self):
        self._save_scene()
        self.close.emit()

    def _scene_selected(self, scene: Scene):
        self._save_scene()
        self._update_view(scene)
