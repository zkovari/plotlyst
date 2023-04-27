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
import copy
from functools import partial
from typing import Optional, List

import qtanim
from PyQt6.QtCore import Qt, QEvent, QObject, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QPushButton, QSizePolicy, QFrame, QButtonGroup, QDialog, QGridLayout, \
    QScrollArea, QApplication, QDialogButtonBox
from overrides import overrides
from qthandy import vspacer, spacer, translucent, transparent, gc, bold, clear_layout, flow, vbox, incr_font, \
    retain_when_hidden, grid, decr_icon, ask_confirmation
from qthandy.filter import OpacityEventFilter

from src.main.python.plotlyst.common import ACT_THREE_COLOR, act_color
from src.main.python.plotlyst.core.domain import StoryStructure, Novel, StoryBeat, \
    SceneType, Scene, TagType, SelectionItem, Tag, \
    StoryBeatType, save_the_cat, three_act_structure, SceneStoryBeat, heros_journey
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_event, EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import NovelStoryStructureUpdated, SceneChangedEvent, SceneDeletedEvent, \
    CharacterChangedEvent, CharacterDeletedEvent
from src.main.python.plotlyst.model.characters_model import CharactersTableModel
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.model.novel import NovelTagsModel
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import link_buttons_to_pages, ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.generated.beat_widget_ui import Ui_BeatWidget
from src.main.python.plotlyst.view.generated.imported_novel_overview_ui import Ui_ImportedNovelOverview
from src.main.python.plotlyst.view.generated.story_structure_selector_dialog_ui import Ui_StoryStructureSelectorDialog
from src.main.python.plotlyst.view.generated.story_structure_settings_ui import Ui_StoryStructureSettings
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.display import Subtitle, IconText
from src.main.python.plotlyst.view.widget.items_editor import ItemsEditorWidget
from src.main.python.plotlyst.view.widget.labels import LabelsEditorWidget
from src.main.python.plotlyst.view.widget.scenes import SceneStoryStructureWidget, SceneSelector


class _StoryStructureButton(QPushButton):
    def __init__(self, structure: StoryStructure, novel: Novel, parent=None):
        super(_StoryStructureButton, self).__init__(parent)
        self._structure = structure
        self.novel = novel
        self.setText(structure.title)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        if self._structure.character_id:
            self.setIcon(avatars.avatar(self._structure.character(self.novel)))
        elif self._structure.icon:
            self.setIcon(IconRegistry.from_name(self._structure.icon, self._structure.icon_color))

        self.setStyleSheet('''
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                                      stop: 0 #f8edeb);
                border: 2px solid #fec89a;
                border-radius: 6px;
                padding: 2px;
            }
            QPushButton:checked {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 0,
                                      stop: 0 #ffd7ba);
                border: 3px solid #FD9235;
                padding: 1px;
            }
            ''')
        self._toggled(self.isChecked())
        self.installEventFilter(OpacityEventFilter(self, 0.7, 0.5, ignoreCheckedButton=True))
        self.toggled.connect(self._toggled)

    def structure(self) -> StoryStructure:
        return self._structure

    def _toggled(self, toggled: bool):
        translucent(self, 1.0 if toggled else 0.5)
        font = self.font()
        font.setBold(toggled)
        self.setFont(font)


class BeatsPreview(QFrame):
    def __init__(self, checkOccupiedBeats: bool = True, parent=None):
        super().__init__(parent)
        self._checkOccupiedBeats = checkOccupiedBeats
        self._layout: QGridLayout = grid(self)
        self._structurePreview: Optional[SceneStoryStructureWidget] = None

        self.setStyleSheet("background-color: rgb(255, 255, 255);")

    def attachStructurePreview(self, structurePreview: SceneStoryStructureWidget):
        self._structurePreview = structurePreview

    def setStructure(self, structure: StoryStructure):
        row = 0
        col = 0
        for beat in structure.beats:
            if beat.type != StoryBeatType.BEAT:
                continue
            wdg = BeatWidget(beat, self._checkOccupiedBeats)
            wdg.setMinimumSize(200, 50)
            if beat.act - 1 > col:  # new act
                self._layout.addWidget(vspacer(), row + 1, col)
                col = beat.act - 1
                row = 0
            self._layout.addWidget(wdg, row, col)
            row += 1
            wdg.beatHighlighted.connect(self._structurePreview.highlightBeat)
            wdg.beatToggled.connect(partial(self._structurePreview.toggleBeatVisibility, beat))


class BeatWidget(QFrame, Ui_BeatWidget, EventListener):
    beatHighlighted = pyqtSignal(StoryBeat)
    beatToggled = pyqtSignal(StoryBeat)

    def __init__(self, beat: StoryBeat, checkOccupiedBeats: bool = True, parent=None):
        super(BeatWidget, self).__init__(parent)
        self.setupUi(self)
        self.beat = beat
        self._checkOccupiedBeats = checkOccupiedBeats

        self.lblTitle.setText(self.beat.text)
        bold(self.lblTitle)
        bold(self.lblSceneTitle)
        self.lblDescription.setText(self.beat.description)
        transparent(self.lblTitle)
        transparent(self.lblDescription)
        transparent(self.btnIcon)
        if beat.icon:
            self.btnIcon.setIcon(IconRegistry.from_name(beat.icon, beat.icon_color))
        self.lblTitle.setStyleSheet(f'QLabel:enabled {{color: {beat.icon_color};}}')

        self.btnSceneSelector = SceneSelector(app_env.novel)
        decr_icon(self.btnSceneSelector, 2)
        retain_when_hidden(self.btnSceneSelector)
        self.layoutRight.insertWidget(0, self.btnSceneSelector,
                                      alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.btnSceneSelector.setHidden(True)
        self.btnSceneSelector.sceneSelected.connect(self._sceneLinked)
        transparent(self.wdgToggleParent)

        retain_when_hidden(self.cbToggle)

        self.cbToggle.setHidden(True)
        if not self._canBeToggled():
            self.cbToggle.setDisabled(True)
        self.cbToggle.toggled.connect(self._beatToggled)
        self.cbToggle.clicked.connect(self._beatClicked)
        self.cbToggle.setChecked(self.beat.enabled)

        self.scene: Optional[Scene] = None
        self.repo = RepositoryPersistenceManager.instance()

        self.refresh()

        self.installEventFilter(self)

        self.textSynopsis.textChanged.connect(self._synopsisEdited)
        event_dispatcher.register(self, SceneChangedEvent)
        event_dispatcher.register(self, SceneDeletedEvent)

    def refresh(self):
        self.stackedWidget.setCurrentWidget(self.pageInfo)
        if not self._checkOccupiedBeats:
            return
        for b in acts_registry.occupied_beats():
            if b.id == self.beat.id:
                self.stackedWidget.setCurrentWidget(self.pageScene)
                self.scene = acts_registry.scene(b)
                if self.scene:
                    self.lblSceneTitle.setText(self.scene.title)
                    self.textSynopsis.setText(self.scene.synopsis)
                    if self.scene.pov:
                        self.btnPov.setIcon(avatars.avatar(self.scene.pov))
                    if self.scene.type == SceneType.ACTION:
                        self.btnSceneType.setIcon(
                            IconRegistry.action_scene_icon(self.scene.outcome_resolution(),
                                                           self.scene.outcome_trade_off()))
                    elif self.scene.type == SceneType.REACTION:
                        self.btnSceneType.setIcon(IconRegistry.reaction_scene_icon())
                else:
                    self.textSynopsis.clear()

    @overrides
    def event_received(self, event: Event):
        self.refresh()

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            if self._canBeToggled() and self._infoPage():
                self.cbToggle.setVisible(True)
            self.btnSceneSelector.setVisible(self._infoPage() and self._checkOccupiedBeats and self.beat.enabled)
            self.setStyleSheet(f'.BeatWidget {{background-color: {act_color(self.beat.act, translucent=True)};}}')
            self.beatHighlighted.emit(self.beat)
        elif event.type() == QEvent.Type.Leave:
            self.cbToggle.setHidden(True)
            self.btnSceneSelector.setHidden(True)
            self.setStyleSheet('.BeatWidget {background-color: white;}')

        return super(BeatWidget, self).eventFilter(watched, event)

    def _infoPage(self) -> bool:
        return self.stackedWidget.currentWidget() == self.pageInfo

    def _scenePage(self) -> bool:
        return self.stackedWidget.currentWidget() == self.pageScene

    def _canBeToggled(self):
        if self.beat.text == 'Midpoint' or self.beat.ends_act:
            return False
        return True

    def _beatToggled(self, toggled: bool):
        translucent(self.lblDescription, 1 if toggled else 0.5)
        self.lblTitle.setEnabled(toggled)
        self.btnIcon.setEnabled(toggled)
        self.lblDescription.setEnabled(toggled)
        bold(self.lblTitle, toggled)

    def _beatClicked(self, checked: bool):
        self.beat.enabled = checked
        self.beatToggled.emit(self.beat)
        self.btnSceneSelector.setVisible(self._infoPage() and self._checkOccupiedBeats and self.beat.enabled)

    def _sceneLinked(self, scene: Scene):
        scene.beats.append(SceneStoryBeat.of(app_env.novel.active_story_structure, self.beat))
        self.repo.update_scene(self.scene)
        emit_event(SceneChangedEvent(self, scene))
        self.refresh()
        qtanim.glow(self.lblTitle, color=QColor(self.beat.icon_color))

    def _synopsisEdited(self):
        if self.scene:
            self.scene.synopsis = self.textSynopsis.toPlainText()
            self.repo.update_scene(self.scene)


class _AbstractStructureEditorWidget(QWidget):
    def __init__(self, novel: Novel, structure: StoryStructure, parent=None):
        super(_AbstractStructureEditorWidget, self).__init__(parent)
        self._structure = structure
        vbox(self)
        self.wdgTitle = IconText(self)
        self.wdgTitle.setText(structure.title)
        if structure.icon:
            self.wdgTitle.setIcon(IconRegistry.from_name(structure.icon, structure.icon_color))
        bold(self.wdgTitle)
        incr_font(self.wdgTitle, 2)

        self.wdgPreview = SceneStoryStructureWidget(self)
        self.wdgPreview.setCheckOccupiedBeats(False)
        self.wdgPreview.setBeatCursor(Qt.CursorShape.ArrowCursor)
        self.wdgPreview.setBeatsMoveable(True)
        self.wdgPreview.setActsClickable(False)
        self.wdgPreview.setActsResizeable(True)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        vbox(self._scroll)

        self.beatsPreview = BeatsPreview(checkOccupiedBeats=False)
        self._scroll.setWidget(self.beatsPreview)
        self.beatsPreview.attachStructurePreview(self.wdgPreview)
        self.wdgPreview.setStructure(novel, self._structure)
        self.beatsPreview.setStructure(self._structure)
        self.layout().addWidget(self.wdgTitle)
        self.layout().addWidget(vspacer(20))
        self.layout().addWidget(self.wdgPreview)
        self.layout().addWidget(self._scroll)
        # self.wdgPreview.actsResized.connect(lambda: emit_event(NovelStoryStructureUpdated(self)))
        # self.wdgPreview.beatMoved.connect(lambda: emit_event(NovelStoryStructureUpdated(self)))

    def structure(self) -> StoryStructure:
        return self._structure


class _ThreeActStructureEditorWidget(_AbstractStructureEditorWidget):
    def __init__(self, novel: Novel, structure: StoryStructure, parent=None):
        super(_ThreeActStructureEditorWidget, self).__init__(novel, structure, parent)


class _SaveTheCatActStructureEditorWidget(_AbstractStructureEditorWidget):
    def __init__(self, novel: Novel, structure: StoryStructure, parent=None):
        super(_SaveTheCatActStructureEditorWidget, self).__init__(novel, structure, parent)


class _HerosJourneyStructureEditorWidget(_AbstractStructureEditorWidget):
    def __init__(self, novel: Novel, structure: StoryStructure, parent=None):
        super(_HerosJourneyStructureEditorWidget, self).__init__(novel, structure, parent)


class StoryStructureSelectorDialog(QDialog, Ui_StoryStructureSelectorDialog):
    def __init__(self, novel: Novel, structure: Optional[StoryStructure] = None, parent=None):
        super(StoryStructureSelectorDialog, self).__init__(parent)
        self.setupUi(self)
        self._novel = novel
        self.setWindowIcon(IconRegistry.story_structure_icon())
        self.btnThreeAct.setIcon(IconRegistry.from_name('mdi.numeric-3-circle-outline', color_on=ACT_THREE_COLOR))
        self.btnSaveTheCat.setIcon(IconRegistry.from_name('fa5s.cat'))
        self.btnHerosJourney.setIcon(IconRegistry.from_name('fa5s.mask'))
        self.buttonGroup.buttonClicked.connect(self._structureChanged)

        self._structure: Optional[StoryStructure] = None
        if structure:
            self.setWindowTitle('Story structure editor')
            self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Ok)
            self.wdgTypesContainer.setHidden(True)
            page, clazz = self._pageAndClass(structure)
            self.__initEditor(structure, page, clazz, copyStructure=False)
        else:
            self._structureChanged()

    def structure(self) -> StoryStructure:
        return self._structure

    @staticmethod
    def display(novel: Novel, structure: Optional[StoryStructure] = None) -> Optional[StoryStructure]:
        dialog = StoryStructureSelectorDialog(novel, structure)
        screen = QApplication.screenAt(dialog.pos())
        if screen:
            dialog.resize(screen.size().width() * 0.9, screen.size().height() * 0.7)
        else:
            dialog.resize(600, 500)

        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return dialog.structure()

        return None

    def _structureChanged(self):
        if self.btnThreeAct.isChecked():
            self.__initEditor(three_act_structure, self.pageThreeAct, _ThreeActStructureEditorWidget)
        elif self.btnSaveTheCat.isChecked():
            self.__initEditor(save_the_cat, self.pageSaveTheCat, _SaveTheCatActStructureEditorWidget)
        elif self.btnHerosJourney.isChecked():
            self.__initEditor(heros_journey, self.pageHerosJourney, _HerosJourneyStructureEditorWidget)

    def __initEditor(self, structure: StoryStructure, page: QWidget, clazz, copyStructure: bool = True):
        self.stackedWidget.setCurrentWidget(page)
        if page.layout().count() == 0:
            if copyStructure:
                self._structure = copy.deepcopy(structure)
            else:
                self._structure = structure
            page.layout().addWidget(clazz(self._novel, self._structure, self))
        else:
            self._structure = page.layout().itemAt(0).widget().structure()

    def _pageAndClass(self, structure: StoryStructure):
        if structure.title == three_act_structure.title:
            return self.pageThreeAct, _ThreeActStructureEditorWidget
        elif structure.title == save_the_cat.title:
            return self.pageSaveTheCat, _SaveTheCatActStructureEditorWidget
        elif structure.title == heros_journey.title:
            return self.pageHerosJourney, _HerosJourneyStructureEditorWidget


class StoryStructureEditor(QWidget, Ui_StoryStructureSettings, EventListener):
    def __init__(self, parent=None):
        super(StoryStructureEditor, self).__init__(parent)
        self.setupUi(self)
        flow(self.wdgTemplates)

        self.btnNew.setIcon(IconRegistry.plus_icon('white'))
        self.btnNew.clicked.connect(self._selectTemplateStructure)

        self.btnDelete.setIcon(IconRegistry.minus_icon())
        self.btnDelete.installEventFilter(ButtonPressResizeEventFilter(self.btnDelete))
        self.btnDelete.clicked.connect(self._removeStructure)
        self.btnCopy.setIcon(IconRegistry.copy_icon())
        self.btnCopy.installEventFilter(ButtonPressResizeEventFilter(self.btnCopy))
        self.btnCopy.clicked.connect(self._duplicateStructure)
        self.btnEdit.setIcon(IconRegistry.edit_icon())
        self.btnEdit.installEventFilter(ButtonPressResizeEventFilter(self.btnEdit))
        self.btnEdit.clicked.connect(self._editStructure)
        self.btnGroupStructure = QButtonGroup()
        self.btnGroupStructure.setExclusive(True)

        self.__initWdgPreview()

        self.novel: Optional[Novel] = None
        self.beats.installEventFilter(self)
        self.repo = RepositoryPersistenceManager.instance()

        event_dispatcher.register(self, CharacterChangedEvent)
        event_dispatcher.register(self, CharacterDeletedEvent)

    @overrides
    def event_received(self, event: Event):
        self._activeStructureToggled(self.novel.active_story_structure, True)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Leave:
            self.wdgPreview.unhighlightBeats()

        return super(StoryStructureEditor, self).eventFilter(watched, event)

    def setNovel(self, novel: Novel):
        self.novel = novel
        for structure in self.novel.story_structures:
            self._addStructureWidget(structure)

    def _addStructureWidget(self, structure: StoryStructure):
        btn = _StoryStructureButton(structure, self.novel)
        btn.toggled.connect(partial(self._activeStructureToggled, structure))
        btn.clicked.connect(partial(self._activeStructureClicked, structure))
        self.btnGroupStructure.addButton(btn)
        self.wdgTemplates.layout().addWidget(btn)
        if structure.active:
            btn.setChecked(True)

        self._toggleDeleteButton()

    def _addNewStructure(self, structure: StoryStructure):
        self.novel.story_structures.append(structure)
        self._addStructureWidget(structure)
        self.btnGroupStructure.buttons()[-1].setChecked(True)
        emit_event(NovelStoryStructureUpdated(self))

    def _removeStructure(self):
        if len(self.novel.story_structures) < 2:
            return

        structure = self.novel.active_story_structure
        if not ask_confirmation(f'Remove structure "{structure.title}"?'):
            return

        to_be_removed_button: Optional[QPushButton] = None
        for btn in self.btnGroupStructure.buttons():
            if btn.structure() is structure:
                to_be_removed_button = btn
                break
        if not to_be_removed_button:
            return

        self.btnGroupStructure.removeButton(to_be_removed_button)
        self.wdgTemplates.layout().removeWidget(to_be_removed_button)
        gc(to_be_removed_button)
        self.novel.story_structures.remove(structure)
        if self.btnGroupStructure.buttons():
            self.btnGroupStructure.buttons()[-1].setChecked(True)
            emit_event(NovelStoryStructureUpdated(self))
        self.repo.update_novel(self.novel)

        self._toggleDeleteButton()

    def _duplicateStructure(self):
        structure = copy.deepcopy(self.novel.active_story_structure)
        self._addNewStructure(structure)
        self._editStructure()

    def _editStructure(self):
        StoryStructureSelectorDialog.display(self.novel, self.novel.active_story_structure)
        self._activeStructureToggled(self.novel.active_story_structure, True)

    def _selectTemplateStructure(self):
        structure: Optional[StoryStructure] = StoryStructureSelectorDialog.display(self.novel)
        if structure:
            self._addNewStructure(structure)

    def _activeStructureToggled(self, structure: StoryStructure, toggled: bool):
        if not toggled:
            return
        clear_layout(self.beats.layout())

        for struct in self.novel.story_structures:
            struct.active = False
        structure.active = True
        acts_registry.refresh()

        if self.wdgPreview.novel is not None:
            item = self.layout().takeAt(1)
            gc(item.widget())
            self.wdgPreview = SceneStoryStructureWidget(self)
            self.__initWdgPreview()
            self.layout().insertWidget(1, self.wdgPreview)
        self.wdgPreview.setStructure(self.novel)
        row = 0
        col = 0
        for beat in structure.beats:
            if beat.type != StoryBeatType.BEAT:
                continue
            wdg = BeatWidget(beat)
            if beat.act - 1 > col:  # new act
                self.beats.layout().addWidget(vspacer(), row + 1, col)
                col = beat.act - 1
                row = 0
            self.beats.layout().addWidget(wdg, row, col)
            row += 1
            wdg.beatHighlighted.connect(self.wdgPreview.highlightBeat)
            wdg.beatToggled.connect(self._beatToggled)

    def __initWdgPreview(self):
        self.wdgPreview.setCheckOccupiedBeats(False)
        self.wdgPreview.setBeatCursor(Qt.CursorShape.ArrowCursor)
        self.wdgPreview.setBeatsMoveable(True)
        self.wdgPreview.setActsClickable(False)
        self.wdgPreview.setActsResizeable(True)
        self.wdgPreview.actsResized.connect(lambda: emit_event(NovelStoryStructureUpdated(self)))
        self.wdgPreview.beatMoved.connect(lambda: emit_event(NovelStoryStructureUpdated(self)))

    def _activeStructureClicked(self, structure: StoryStructure, toggled: bool):
        if not toggled:
            return

        self.repo.update_novel(self.novel)
        emit_event(NovelStoryStructureUpdated(self))

    def _beatToggled(self, beat: StoryBeat):
        self.wdgPreview.toggleBeatVisibility(beat)
        self.repo.update_novel(self.novel)

    def _toggleDeleteButton(self):
        self.btnDelete.setEnabled(len(self.novel.story_structures) > 1)


class TagLabelsEditor(LabelsEditorWidget):

    def __init__(self, novel: Novel, tagType: TagType, tags: List[Tag], parent=None):
        self.novel = novel
        self.tagType = tagType
        self.tags = tags
        super(TagLabelsEditor, self).__init__(checkable=False, parent=parent)
        self.btnEdit.setIcon(IconRegistry.tag_plus_icon())
        self.editor.model.item_edited.connect(self._updateTags)
        self.editor.model.modelReset.connect(self._updateTags)
        self._updateTags()

    @overrides
    def _initPopupWidget(self) -> QWidget:
        self.editor: ItemsEditorWidget = super(TagLabelsEditor, self)._initPopupWidget()
        self.editor.setBgColorFieldEnabled(True)
        return self.editor

    @overrides
    def _initModel(self) -> SelectionItemsModel:
        return NovelTagsModel(self.novel, self.tagType, self.tags)

    @overrides
    def items(self) -> List[SelectionItem]:
        return self.tags

    def _updateTags(self):
        self._wdgLabels.clear()
        self._addItems(self.tags)


class TagTypeDisplay(QWidget):
    def __init__(self, novel: Novel, tagType: TagType, parent=None):
        super(TagTypeDisplay, self).__init__(parent)
        self.tagType = tagType
        self.novel = novel

        vbox(self)
        self.subtitle = Subtitle(self)
        self.subtitle.lblTitle.setText(tagType.text)
        self.subtitle.lblDescription.setText(tagType.description)
        if tagType.icon:
            self.subtitle.setIconName(tagType.icon, tagType.icon_color)
        self.labelsEditor = TagLabelsEditor(self.novel, tagType, self.novel.tags[tagType])
        self.layout().addWidget(self.subtitle)
        self.layout().addWidget(group(spacer(20), self.labelsEditor))


class TagsEditor(QWidget):
    def __init__(self, parent=None):
        super(TagsEditor, self).__init__(parent)
        self.novel: Optional[Novel] = None
        vbox(self)

    def setNovel(self, novel: Novel):
        self.novel = novel

        for tag_type in self.novel.tags.keys():
            self.layout().addWidget(TagTypeDisplay(self.novel, tag_type, self))
        self.layout().addWidget(vspacer())


class ImportedNovelOverview(QWidget, Ui_ImportedNovelOverview):
    def __init__(self, parent=None):
        super(ImportedNovelOverview, self).__init__(parent)
        self.setupUi(self)
        self.btnCharacters.setIcon(IconRegistry.character_icon())
        self.btnLocations.setIcon(IconRegistry.location_icon())
        self.btnLocations.setHidden(True)
        self.btnScenes.setIcon(IconRegistry.scene_icon())
        transparent(self.btnTitle)
        self.btnTitle.setIcon(IconRegistry.book_icon())
        bold(self.btnTitle)

        link_buttons_to_pages(self.stackedWidget,
                              [(self.btnCharacters, self.pageCharacters), (self.btnLocations, self.pageLocations),
                               (self.btnScenes, self.pageScenes)])

        self._charactersModel: Optional[CharactersTableModel] = None

    def setNovel(self, novel: Novel):
        self.btnTitle.setText(novel.title)

        if novel.characters:
            self._charactersModel = CharactersTableModel(novel)
            self.lstCharacters.setModel(self._charactersModel)
            self.btnCharacters.setChecked(True)
        else:
            self.btnCharacters.setDisabled(True)

        self.treeChapters.setNovel(novel, readOnly=True)
