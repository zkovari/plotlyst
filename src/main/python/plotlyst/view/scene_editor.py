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
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QTableView
from overrides import overrides
from qtanim import fade_in
from qthandy import underline, incr_font, margins, pointy, hbox, clear_layout, busy
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Scene, Document, StoryBeat, \
    Character, ScenePurposeType, ScenePurpose, Plot, ScenePlotReference, NovelSetting
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event, emit_event
from src.main.python.plotlyst.event.handler import event_dispatchers
from src.main.python.plotlyst.events import NovelAboutToSyncEvent, SceneStoryBeatChangedEvent, \
    NovelStorylinesToggleEvent, NovelStructureToggleEvent, NovelPovTrackingToggleEvent
from src.main.python.plotlyst.model.characters_model import CharactersSceneAssociationTableModel
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import emoji_font, ButtonPressResizeEventFilter, set_tab_icon, \
    push_btn, fade_out_and_gc
from src.main.python.plotlyst.view.generated.scene_editor_ui import Ui_SceneEditor
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorMenu
from src.main.python.plotlyst.view.widget.labels import CharacterLabel
from src.main.python.plotlyst.view.widget.scene.editor import ScenePurposeSelectorWidget, ScenePurposeTypeButton, \
    SceneStorylineEditor, SceneAgendaEditor, SceneElementWidget
from src.main.python.plotlyst.view.widget.scene.plot import ScenePlotLabels, \
    ScenePlotSelectorMenu
from src.main.python.plotlyst.view.widget.scene.reader_drive import ReaderCuriosityEditor, ReaderInformationEditor


class SceneEditor(QObject, EventListener):
    close = pyqtSignal()

    def __init__(self, novel: Novel):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_SceneEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel
        self.scene: Optional[Scene] = None
        self.notes_updated: bool = False

        self._emoji_font = emoji_font()

        set_tab_icon(self.ui.tabWidget, self.ui.tabStorylines,
                     IconRegistry.storylines_icon(color_on=PLOTLYST_SECONDARY_COLOR))
        set_tab_icon(self.ui.tabWidget, self.ui.tabDrive,
                     IconRegistry.from_name('mdi.chemical-weapon', color_on=PLOTLYST_SECONDARY_COLOR))
        set_tab_icon(self.ui.tabWidget, self.ui.tabStructure,
                     IconRegistry.from_name('mdi6.timeline-outline', rotated=90, color_on=PLOTLYST_SECONDARY_COLOR))
        set_tab_icon(self.ui.tabWidget, self.ui.tabNotes, IconRegistry.document_edition_icon())
        set_tab_icon(self.ui.tabWidgetDrive, self.ui.tabAgency, IconRegistry.character_icon())
        set_tab_icon(self.ui.tabWidgetDrive, self.ui.tabCuriosity,
                     IconRegistry.from_name('ei.question-sign', color_on=PLOTLYST_SECONDARY_COLOR))
        set_tab_icon(self.ui.tabWidgetDrive, self.ui.tabInformation,
                     IconRegistry.from_name('fa5s.book-reader', color_on=PLOTLYST_SECONDARY_COLOR))

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
        self.ui.wdgStructure.setVisible(self.novel.prefs.toggled(NovelSetting.Structure))

        self._povMenu = CharacterSelectorMenu(self.novel, self.ui.wdgPov.btnAvatar)
        self._povMenu.selected.connect(self._pov_changed)
        self.ui.wdgPov.btnAvatar.setText('POV')
        self.ui.wdgPov.setFixedSize(170, 170)

        self.ui.textNotes.setTitleVisible(False)
        self.ui.textNotes.setPlaceholderText("Scene notes")

        self.tblCharacters = QTableView()
        self.tblCharacters.setShowGrid(False)
        self.tblCharacters.verticalHeader().setVisible(False)
        self.tblCharacters.horizontalHeader().setVisible(False)
        self.tblCharacters.horizontalHeader().setDefaultSectionSize(200)
        pointy(self.tblCharacters)

        self._characters_model = CharactersSceneAssociationTableModel(self.novel)
        self._characters_model.selection_changed.connect(self._character_changed)
        self.tblCharacters.setModel(self._characters_model)
        self.tblCharacters.clicked.connect(self._characters_model.toggleSelection)

        self.ui.btnEditCharacters.setIcon(IconRegistry.plus_edit_icon())
        menu = MenuWidget(self.ui.btnEditCharacters)
        menu.addWidget(self.tblCharacters)
        self.ui.btnEditCharacters.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnEditCharacters))
        self.ui.btnStageCharacterLabel.clicked.connect(lambda: menu.exec())

        # self.tag_selector = SceneTagSelector(self.novel, self.scene)
        # self.ui.wdgTags.layout().addWidget(self.tag_selector)

        self.ui.treeScenes.setNovel(self.novel, readOnly=True)
        self.ui.treeScenes.sceneSelected.connect(self._scene_selected)

        self._purposeSelector = ScenePurposeSelectorWidget()
        margins(self._purposeSelector, top=25)
        self.ui.pagePurpose.layout().addWidget(self._purposeSelector)
        self._purposeSelector.skipped.connect(self._purpose_skipped)
        self._purposeSelector.selected.connect(self._purpose_changed)

        self._btnPurposeType = ScenePurposeTypeButton()
        self._btnPurposeType.reset.connect(self._reset_purpose_editor)
        self.ui.wdgMidbar.layout().insertWidget(0, self._btnPurposeType)

        self.ui.btnInfo.setHidden(True)

        self._btnPlotSelector = push_btn(IconRegistry.storylines_icon(), 'Storylines',
                                         tooltip='Link storylines to this scene', transparent_=True)
        self._btnPlotSelector.installEventFilter(OpacityEventFilter(self._btnPlotSelector, leaveOpacity=0.8))
        self._plotSelectorMenu = ScenePlotSelectorMenu(self.novel, self._btnPlotSelector)
        self._plotSelectorMenu.plotSelected.connect(self._storyline_selected)
        hbox(self.ui.wdgStorylines)
        self.ui.wdgMidbar.layout().insertWidget(1, self._btnPlotSelector)

        self._storylineEditor = SceneStorylineEditor(self.novel)
        self._storylineEditor.outcomeChanged.connect(self._btnPurposeType.refresh)
        self._storylineEditor.outcomeChanged.connect(self.ui.wdgSceneStructure.refreshOutcome)
        self._storylineEditor.storylineLinked.connect(self._storyline_linked)
        self._storylineEditor.storylineEditRequested.connect(self._storyline_edit)
        self.ui.tabStorylines.layout().addWidget(self._storylineEditor)

        self._agencyEditor = SceneAgendaEditor(self.novel)
        self._agencyEditor.setUnsetCharacterSlot(self._character_not_selected_notification)
        self.ui.tabAgency.layout().addWidget(self._agencyEditor)

        self._curiosityEditor = ReaderCuriosityEditor(self.novel)
        self.ui.tabCuriosity.layout().addWidget(self._curiosityEditor)

        self._informationEditor = ReaderInformationEditor(self.novel)
        self.ui.tabInformation.layout().addWidget(self._informationEditor)

        self.ui.btnClose.clicked.connect(self._on_close)

        self.ui.wdgSceneStructure.timeline.outcomeChanged.connect(self._btnPurposeType.refresh)
        self.ui.wdgSceneStructure.timeline.outcomeChanged.connect(self._storylineEditor.refresh)

        self.ui.tabWidget.setCurrentWidget(self.ui.tabDrive)
        self.ui.tabWidgetDrive.setCurrentWidget(self.ui.tabCuriosity)
        self.ui.tabWidget.currentChanged.connect(self._page_toggled)

        self.repo = RepositoryPersistenceManager.instance()

        self.ui.wdgPov.setVisible(self.novel.prefs.toggled(NovelSetting.Track_pov))

        dispatcher = event_dispatchers.instance(self.novel)
        dispatcher.register(self, NovelAboutToSyncEvent, NovelStorylinesToggleEvent, NovelStructureToggleEvent, NovelPovTrackingToggleEvent)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, NovelAboutToSyncEvent):
            self._on_close()
        elif isinstance(event, NovelStorylinesToggleEvent):
            self.ui.wdgStorylines.setVisible(event.toggled)
            self._btnPlotSelector.setVisible(event.toggled)
            self._storylineEditor.storylinesSettingToggledEvent(event.toggled)
        elif isinstance(event, NovelStructureToggleEvent):
            self.ui.wdgStructure.setVisible(event.toggled)
        elif isinstance(event, NovelPovTrackingToggleEvent):
            self.ui.wdgPov.setVisible(event.toggled)

    def set_scene(self, scene: Scene):
        self.scene = scene
        self.ui.treeScenes.refresh()
        self.ui.treeScenes.selectScene(self.scene)

        self._update_pov_avatar()
        self.ui.sbDay.setValue(self.scene.day)

        self.ui.wdgSceneStructure.setScene(self.novel, self.scene)
        # self.tag_selector.setScene(self.scene)
        self._storylineEditor.setScene(self.scene)
        self._agencyEditor.setScene(self.scene)
        self._curiosityEditor.setScene(self.scene)
        self._informationEditor.setScene(self.scene)

        self.ui.lineTitle.setText(self.scene.title)
        self.ui.textSynopsis.setText(self.scene.synopsis)

        self.ui.wdgStructure.unhighlightBeats()
        self.ui.wdgStructure.highlightScene(self.scene)
        self.ui.wdgStructure.uncheckActs()
        self.ui.wdgStructure.setActChecked(acts_registry.act(self.scene))

        self.notes_updated = False
        if self.ui.tabWidget.currentWidget() is self.ui.tabNotes or (
                self.scene.document and self.scene.document.loaded):
            self._update_notes()
        else:
            self.ui.textNotes.clear()

        self._btnPurposeType.setScene(self.scene)
        if self.scene.purpose is None:
            self._reset_purpose_editor()
        else:
            self._close_purpose_editor()

        self._plotSelectorMenu.setScene(self.scene)
        clear_layout(self.ui.wdgStorylines)
        for ref in self.scene.plot_values:
            self._add_plot_ref(ref)

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

    def _character_not_selected_notification(self):
        qtanim.shake(self.ui.wdgPov)
        qtanim.shake(self.ui.btnStageCharacterLabel)

    def _pov_changed(self, pov: Character):
        self.scene.pov = pov

        self._agencyEditor.povChangedEvent(pov)

        self._update_pov_avatar()
        self._characters_model.update()
        self._character_changed()
        self.ui.treeScenes.refreshScene(self.scene)

    def _update_pov_avatar(self):
        if self.scene.pov:
            self.ui.wdgPov.setCharacter(self.scene.pov)
            self.ui.wdgPov.btnAvatar.setToolTip(f'<html>Point of view character: <b>{self.scene.pov.name}</b>')
        else:
            self.ui.wdgPov.reset()
            self.ui.wdgPov.btnAvatar.setToolTip('Select point of view character')

    def _storyline_selected(self, storyline: Plot) -> ScenePlotLabels:
        plotRef = ScenePlotReference(storyline)
        self.scene.plot_values.append(plotRef)
        return self._add_plot_ref(plotRef)

    def _storyline_removed(self, labels: ScenePlotLabels, plotRef: ScenePlotReference):
        fade_out_and_gc(self.ui.wdgStorylines.layout(), labels)
        self.scene.plot_values.remove(plotRef)

    def _storyline_linked(self, element: SceneElementWidget, storyline: Plot):
        if next((x for x in self.scene.plot_values if x.plot.id == storyline.id), None) is None:
            labels = self._storyline_selected(storyline)
            qtanim.glow(labels.icon(), loop=3, color=QColor(storyline.icon_color))

    def _storyline_edit(self, element: SceneElementWidget, storyline: Plot):
        for i in range(self.ui.wdgStorylines.layout().count()):
            item = self.ui.wdgStorylines.layout().itemAt(i)
            if item and isinstance(item.widget(),
                                   ScenePlotLabels) and item.widget().storylineRef().plot.id == storyline.id:
                item.widget().activate()

    def _add_plot_ref(self, plotRef: ScenePlotReference) -> ScenePlotLabels:
        labels = ScenePlotLabels(plotRef)
        labels.reset.connect(partial(self._storyline_removed, labels, plotRef))
        self.ui.wdgStorylines.layout().addWidget(labels)
        self._btnPlotSelector.setText('')

        return labels

    def _title_edited(self, text: str):
        self.scene.title = text
        self.ui.treeScenes.refreshScene(self.scene)

    def _character_changed(self):
        self.ui.wdgCharacters.clear()

        for character in self.scene.characters:
            self.ui.wdgCharacters.addLabel(CharacterLabel(character))

        self._agencyEditor.updateAvailableCharacters()

    def _purpose_skipped(self):
        self.scene.purpose = ScenePurposeType.Other
        self._close_purpose_editor()

    def _purpose_changed(self, purpose: ScenePurpose):
        self.scene.purpose = purpose.type
        self._close_purpose_editor()

    def _close_purpose_editor(self):
        self._btnPurposeType.refresh()
        if not self._btnPurposeType.isVisible():
            fade_in(self._btnPurposeType)
        # if not self.ui.btnInfo.isVisible():
        #     fade_in(self.ui.btnInfo)
        self.ui.wdgStorylines.setVisible(self.novel.prefs.toggled(NovelSetting.Storylines))
        self._btnPlotSelector.setVisible(self.novel.prefs.toggled(NovelSetting.Storylines))
        # to avoid segfault for some reason, we disable it first before changing the stack widget
        self._purposeSelector.setDisabled(True)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEditor)
        self._storylineEditor.purposeChangedEvent()

    def _reset_purpose_editor(self):
        self.scene.purpose = None
        self._btnPurposeType.setHidden(True)
        self.ui.btnInfo.setHidden(True)
        self.ui.wdgStorylines.setHidden(True)
        self._btnPlotSelector.setHidden(True)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pagePurpose)
        self._purposeSelector.setEnabled(True)

    def _save_scene(self):
        self.scene.title = self.ui.lineTitle.text()
        self.scene.synopsis = self.ui.textSynopsis.toPlainText()
        self.scene.day = self.ui.sbDay.value()

        self.scene.tag_references.clear()
        # for tag in self.tag_selector.tags():
        #     self.scene.tag_references.append(TagReference(tag.id))

        #     self.novel.scenes.append(self.scene)
        #     self.repo.insert_scene(self.novel, self.scene)
        # else:
        self.repo.update_scene(self.scene)

        if not self.scene.document:
            self.scene.document = Document('', scene_id=self.scene.id)
            self.scene.document.loaded = True

        if self.scene.document.loaded:
            self.scene.document.content = self.ui.textNotes.textEdit.toHtml()
            self.repo.update_doc(self.novel, self.scene.document)

    def _on_close(self):
        self._save_scene()
        self.close.emit()

    @busy
    def _scene_selected(self, scene: Scene):
        self._save_scene()
        QTimer.singleShot(10, lambda: self.set_scene(scene))
