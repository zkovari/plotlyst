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
from typing import Optional

import emoji
import qtanim
from PyQt6.QtCore import QObject, pyqtSignal, QModelIndex, QItemSelectionModel, \
    Qt
from PyQt6.QtWidgets import QWidget, QWidgetAction, QTableView, QMenu
from fbs_runtime import platform
from qthandy import flow, clear_layout

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Scene, Document, StoryBeat, \
    SceneStoryBeat, SceneStructureAgenda, Character, ScenePlotReference, TagReference
from src.main.python.plotlyst.event.core import emit_info
from src.main.python.plotlyst.model.characters_model import CharactersSceneAssociationTableModel
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import emoji_font
from src.main.python.plotlyst.view.generated.scene_editor_ui import Ui_SceneEditor
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.input import RotatedButtonOrientation
from src.main.python.plotlyst.view.widget.labels import CharacterLabel
from src.main.python.plotlyst.view.widget.scenes import ScenePlotSelector, SceneTagSelector


class SceneEditor(QObject):
    commands_sent = pyqtSignal(QWidget, list)

    def __init__(self, novel: Novel, scene: Optional[Scene] = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_SceneEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel
        self.scene: Optional[Scene] = None
        self.notes_updated: bool = False

        if platform.is_windows():
            self._emoji_font = emoji_font(14)
        else:
            self._emoji_font = emoji_font(20)

        self.ui.btnAttributes.setOrientation(RotatedButtonOrientation.VerticalBottomToTop)
        self.ui.btnAttributes.setIcon(IconRegistry.from_name('fa5s.yin-yang'))
        self.ui.btnNotes.setOrientation(RotatedButtonOrientation.VerticalBottomToTop)
        self.ui.btnNotes.setIcon(IconRegistry.document_edition_icon())
        self.ui.btnDrive.setIcon(IconRegistry.from_name('mdi.chemical-weapon'))
        self.ui.btnDrive.setOrientation(RotatedButtonOrientation.VerticalBottomToTop)

        self.ui.btnStageCharacterLabel.setIcon(IconRegistry.character_icon(color_on='black'))
        self.ui.btnEditCharacters.setIcon(IconRegistry.plus_edit_icon())

        self.ui.lblDayEmoji.setFont(self._emoji_font)
        self.ui.lblDayEmoji.setText(emoji.emojize(':spiral_calendar:'))
        self.ui.lblTitleEmoji.setFont(self._emoji_font)
        self.ui.lblTitleEmoji.setText(emoji.emojize(':clapper_board:'))
        self.ui.lblSynopsisEmoji.setFont(self._emoji_font)
        self.ui.lblSynopsisEmoji.setText(emoji.emojize(':scroll:'))
        self.ui.lblPlotEmoji.setFont(self._emoji_font)
        self.ui.lblPlotEmoji.setText(emoji.emojize(':chart_increasing:'))

        self.ui.wdgStructure.setBeatsCheckable(True)
        self.ui.wdgStructure.setStructure(self.novel)
        self.ui.wdgStructure.setActsClickable(False)
        self.ui.wdgStructure.beatSelected.connect(self._beat_selected)
        self.ui.wdgStructure.setRemovalContextMenuEnabled(True)
        self.ui.wdgStructure.beatRemovalRequested.connect(self._beat_removed)

        self._povMenu = QMenu(self.ui.wdgPov.btnPov)
        for char in self.novel.characters:
            self._povMenu.addAction(avatars.avatar(char), char.name, partial(self._on_pov_changed, char))
        self.ui.wdgPov.btnPov.setMenu(self._povMenu)
        self.ui.wdgPov.btnPov.setText('Select POV')

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

        action = QWidgetAction(self.ui.btnEditCharacters)
        action.setDefaultWidget(self.tblCharacters)
        self.ui.btnEditCharacters.addAction(action)

        self.tag_selector = SceneTagSelector(self.novel, self.scene)
        self.ui.wdgTags.layout().addWidget(self.tag_selector)

        self.scenes_model = ScenesTableModel(self.novel)
        self.ui.lstScenes.setModel(self.scenes_model)
        self.ui.lstScenes.setModelColumn(ScenesTableModel.ColTitle)
        self.ui.lstScenes.clicked.connect(self._new_scene_selected)

        self.ui.btnClose.setIcon(IconRegistry.return_icon())
        self.ui.btnClose.clicked.connect(self._on_close)
        self.ui.btnPrevious.setIcon(IconRegistry.arrow_left_thick_icon())
        self.ui.btnPrevious.clicked.connect(self._on_previous_scene)
        self.ui.btnNext.setIcon(IconRegistry.arrow_right_thick_icon())
        self.ui.btnNext.clicked.connect(self._on_next_scene)

        flow(self.ui.wdgPlotContainer)

        self.ui.wdgSceneStructure.setUnsetCharacterSlot(self._pov_not_selected_notification)
        self.ui.pageDrive.setStyleSheet(f'#pageDrive {{background-color: {RELAXED_WHITE_COLOR};}}')

        self._update_view(scene)

        self.ui.btnGroupPages.buttonToggled.connect(self._page_toggled)

        self.repo = RepositoryPersistenceManager.instance()
        self.ui.btnAttributes.setChecked(True)

    def _update_view(self, scene: Optional[Scene] = None):
        if scene:
            self.scene = scene
            self._new_scene = False
            index = self.scenes_model.index(self.novel.scenes.index(scene), ScenesTableModel.ColTitle)
            self.ui.lstScenes.selectionModel().select(index, QItemSelectionModel.Select)
        else:
            self.scene = Scene('')
            if len(self.novel.scenes) > 1:
                self.scene.day = self.novel.scenes[-1].day
            self.scene.agendas.append(SceneStructureAgenda())
            self._new_scene = True

        if self.scene.pov:
            for agenda in self.scene.agendas:
                if not agenda.character_id:
                    agenda.character_id = self.scene.pov.id
        self._update_pov_avatar()
        self.ui.sbDay.setValue(self.scene.day)

        self.ui.wdgSceneStructure.setScene(self.novel, self.scene)
        clear_layout(self.ui.wdgPlotContainer)
        for plot_v in self.scene.plot_values:
            self._add_plot_selector(plot_v)
        self._add_plot_selector()

        self.tag_selector.setScene(self.scene)

        self.ui.lineTitle.setText(self.scene.title)
        self.ui.textSynopsis.setText(self.scene.synopsis)

        self.ui.wdgStructure.unhighlightBeats()
        if not self._new_scene:
            self.ui.wdgStructure.highlightScene(self.scene)
        self.ui.wdgStructure.uncheckActs()
        self.ui.wdgStructure.setActChecked(acts_registry.act(self.scene))

        self.notes_updated = False
        if self.ui.btnNotes.isChecked() or (self.scene.document and self.scene.document.loaded):
            self._update_notes()
        else:
            self.ui.textNotes.clear()

        self._characters_model.setScene(self.scene)
        self._character_changed()

        self.ui.wdgDriveEditor.setScene(self.scene)

        if self._new_scene:
            self.ui.btnPrevious.setDisabled(True)
            self.ui.btnPrevious.setHidden(True)
            self.ui.btnNext.setDisabled(True)
            self.ui.btnNext.setHidden(True)
        else:
            index = self.novel.scenes.index(scene)
            if index == 0:
                self.ui.btnPrevious.setDisabled(True)
            else:
                self.ui.btnPrevious.setEnabled(True)
            if index == len(self.novel.scenes) - 1:
                self.ui.btnNext.setDisabled(True)
            else:
                self.ui.btnNext.setEnabled(True)

    def _page_toggled(self):
        if self.ui.btnAttributes.isChecked():
            self.ui.stackedWidget.setCurrentWidget(self.ui.pageStructure)
        elif self.ui.btnNotes.isChecked():
            self.ui.stackedWidget.setCurrentWidget(self.ui.pageNotes)
            self._update_notes()
        elif self.ui.btnDrive.isChecked():
            self.ui.stackedWidget.setCurrentWidget(self.ui.pageDrive)

    def _beat_selected(self, beat: StoryBeat):
        if self.scene.beat(self.novel) and self.scene.beat(self.novel) != beat:
            self.ui.wdgStructure.toggleBeat(self.scene.beat(self.novel), False)
            self.scene.remove_beat(self.novel)
        self.scene.beats.append(SceneStoryBeat.of(self.novel.active_story_structure, beat))
        self.ui.wdgStructure.highlightScene(self.scene)

    def _beat_removed(self, beat: StoryBeat):
        if self.scene.beat(self.novel) == beat:
            self.scene.remove_beat(self.novel)
            self.ui.wdgStructure.unhighlightBeats()
            self.ui.wdgStructure.toggleBeat(beat, False)
            self.ui.wdgStructure.highlightScene(self.scene)

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

    def _add_plot_selector(self, plot_value: Optional[ScenePlotReference] = None):
        if plot_value or len(self.novel.plots) > len(self.scene.plot_values):
            plot_selector = ScenePlotSelector(self.novel, self.scene, simplified=len(self.scene.plot_values) > 0)
            plot_selector.plotSelected.connect(self._add_plot_selector)
            if plot_value:
                plot_selector.setPlot(plot_value)
            self.ui.wdgPlotContainer.layout().addWidget(plot_selector)

    def _on_pov_changed(self, pov: Character):
        self.scene.pov = pov

        self.scene.agendas[0].character_id = self.scene.pov.id
        self.scene.agendas[0].conflict_references.clear()

        self._update_pov_avatar()
        self._characters_model.update()
        self._character_changed()
        self.ui.wdgSceneStructure.updateAgendaCharacter()

    def _update_pov_avatar(self):
        if self.scene.pov:
            self.ui.wdgPov.setCharacter(self.scene.pov)
            self.ui.wdgPov.btnPov.setToolTip(f'<html>Point of view character: <b>{self.scene.pov.name}</b>')
        else:
            self.ui.wdgPov.reset()
            self.ui.wdgPov.btnPov.setToolTip('Select point of view character')

    def _character_changed(self):
        self.ui.wdgCharacters.clear()

        for character in self.scene.characters:
            self.ui.wdgCharacters.addLabel(CharacterLabel(character))

        self.ui.wdgSceneStructure.updateAvailableAgendaCharacters()

    def _save_scene(self):
        self.scene.title = self.ui.lineTitle.text()
        self.scene.synopsis = self.ui.textSynopsis.toPlainText()
        self.ui.wdgSceneStructure.updateAgendas()
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

    def _on_previous_scene(self):
        row = self.novel.scenes.index(self.scene) - 1
        self.ui.lstScenes.selectionModel().select(self.scenes_model.index(row, ScenesTableModel.ColTitle),
                                                  QItemSelectionModel.ClearAndSelect)
        self._new_scene_selected(self.scenes_model.index(row, 0))

    def _on_next_scene(self):
        row = self.novel.scenes.index(self.scene) + 1
        self.ui.lstScenes.selectionModel().select(self.scenes_model.index(row, ScenesTableModel.ColTitle),
                                                  QItemSelectionModel.ClearAndSelect)
        self._new_scene_selected(self.scenes_model.index(row, 0))

    def _new_scene_selected(self, index: QModelIndex):
        self._save_scene()

        scene = self.scenes_model.data(index, role=ScenesTableModel.SceneRole)
        self._update_view(scene)
