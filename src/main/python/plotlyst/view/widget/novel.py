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
import copy
from functools import partial
from typing import Optional, List

import qtanim
from PyQt6.QtCore import Qt, QEvent, QObject, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QPushButton, QSizePolicy, QFrame, QButtonGroup, QHeaderView, QMenu, QWidgetAction, \
    QDialog
from overrides import overrides
from qthandy import vspacer, spacer, translucent, transparent, btn_popup, gc, bold, clear_layout, flow, vbox, incr_font, \
    margins, italic, btn_popup_menu, ask_confirmation, retain_when_hidden
from qthandy.filter import VisibilityToggleEventFilter, OpacityEventFilter

from src.main.python.plotlyst.common import ACT_THREE_COLOR
from src.main.python.plotlyst.core.domain import StoryStructure, Novel, StoryBeat, \
    Character, SceneType, Scene, TagType, SelectionItem, Tag, \
    StoryBeatType, Plot, PlotType, PlotValue, three_act_structure, save_the_cat
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import emit_event, EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import NovelStoryStructureUpdated, SceneChangedEvent, SceneDeletedEvent
from src.main.python.plotlyst.model.chapters_model import ChaptersTreeModel
from src.main.python.plotlyst.model.characters_model import CharactersTableModel
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.model.novel import NovelTagsModel
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager, delete_plot
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES
from src.main.python.plotlyst.view.common import link_buttons_to_pages, action
from src.main.python.plotlyst.view.dialog.novel import PlotValueEditorDialog
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.generated.beat_widget_ui import Ui_BeatWidget
from src.main.python.plotlyst.view.generated.imported_novel_overview_ui import Ui_ImportedNovelOverview
from src.main.python.plotlyst.view.generated.plot_editor_widget_ui import Ui_PlotEditor
from src.main.python.plotlyst.view.generated.plot_widget_ui import Ui_PlotWidget
from src.main.python.plotlyst.view.generated.story_structure_character_link_widget_ui import \
    Ui_StoryStructureCharacterLink
from src.main.python.plotlyst.view.generated.story_structure_selector_dialog_ui import Ui_StoryStructureSelectorDialog
from src.main.python.plotlyst.view.generated.story_structure_settings_ui import Ui_StoryStructureSettings
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.display import Subtitle
from src.main.python.plotlyst.view.widget.items_editor import ItemsEditorWidget
from src.main.python.plotlyst.view.widget.labels import LabelsEditorWidget, PlotValueLabel
from src.main.python.plotlyst.view.widget.scenes import SceneStoryStructureWidget
from src.main.python.plotlyst.view.widget.utility import ColorPicker


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


class BeatWidget(QFrame, Ui_BeatWidget, EventListener):
    beatHighlighted = pyqtSignal(StoryBeat)
    beatToggled = pyqtSignal(StoryBeat)

    def __init__(self, beat: StoryBeat, parent=None):
        super(BeatWidget, self).__init__(parent)
        self.setupUi(self)
        self.beat = beat
        self.lblTitle.setText(self.beat.text)
        bold(self.lblTitle)
        self.lblDescription.setText(self.beat.description)
        transparent(self.lblTitle)
        transparent(self.lblDescription)
        transparent(self.btnIcon)
        if beat.icon:
            self.btnIcon.setIcon(IconRegistry.from_name(beat.icon, beat.icon_color))
        self.lblTitle.setStyleSheet(f'color: {beat.icon_color};')

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
            self.setStyleSheet('.BeatWidget {background-color: #DBF5FA;}')
            self.beatHighlighted.emit(self.beat)
        elif event.type() == QEvent.Type.Leave:
            if self._canBeToggled() and self._infoPage():
                self.cbToggle.setHidden(True)
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
        translucent(self, 1 if toggled else 0.5)
        bold(self.lblTitle, toggled)

    def _beatClicked(self, checked: bool):
        self.beat.enabled = checked
        self.beatToggled.emit(self.beat)

    def _synopsisEdited(self):
        if self.scene:
            self.scene.synopsis = self.textSynopsis.toPlainText()
            self.repo.update_scene(self.scene)


class StoryStructureCharacterLinkWidget(QWidget, Ui_StoryStructureCharacterLink, EventListener):
    linkCharacter = pyqtSignal(Character)
    unlinkCharacter = pyqtSignal(Character)

    def __init__(self, novel: Novel, parent=None):
        super(StoryStructureCharacterLinkWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.wdgCharacters.setExclusive(False)
        self.wdgCharacters.setCharacters(novel.characters, checkAll=False)
        self.wdgCharacters.characterToggled.connect(self._characterToggled)
        event_dispatcher.register(self, NovelStoryStructureUpdated)

        self.refresh()

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, NovelStoryStructureUpdated):
            self.refresh()

    def refresh(self):
        self.wdgCharacters.clear()
        for char in self.novel.characters:
            if char is self.novel.active_story_structure.character(self.novel):
                self.wdgCharacters.addCharacter(char)
            else:
                self.wdgCharacters.addCharacter(char, checked=False)

    def _characterToggled(self, character: Character, toggled: bool):
        if toggled:
            self.linkCharacter.emit(character)
        else:
            self.unlinkCharacter.emit(character)


class _AbstractStructureEditorWidget(QWidget):
    def __init__(self, parent=None):
        super(_AbstractStructureEditorWidget, self).__init__(parent)
        vbox(self)
        self.wdgPreview = SceneStoryStructureWidget(self)
        self.wdgPreview.setCheckOccupiedBeats(False)
        self.wdgPreview.setBeatCursor(Qt.CursorShape.ArrowCursor)
        self.wdgPreview.setBeatsMoveable(True)
        self.wdgPreview.setActsClickable(False)
        self.wdgPreview.setActsResizeable(True)
        # self.wdgPreview.actsResized.connect(lambda: emit_event(NovelStoryStructureUpdated(self)))
        # self.wdgPreview.beatMoved.connect(lambda: emit_event(NovelStoryStructureUpdated(self)))


class _ThreeActStructureEditorWidget(_AbstractStructureEditorWidget):
    def __init__(self, novel: Novel, parent=None):
        super(_ThreeActStructureEditorWidget, self).__init__(parent)
        self.wdgPreview.setStructure(novel, copy.deepcopy(three_act_structure))
        self.layout().addWidget(self.wdgPreview)


class StoryStructureSelectorDialog(QDialog, Ui_StoryStructureSelectorDialog):
    def __init__(self, novel: Novel, parent=None):
        super(StoryStructureSelectorDialog, self).__init__(parent)
        self.setupUi(self)
        self._novel = novel
        self.setWindowIcon(IconRegistry.story_structure_icon())
        self.btnThreeAct.setIcon(IconRegistry.from_name('mdi.numeric-3-circle-outline', color_on=ACT_THREE_COLOR))
        self.btnSaveTheCat.setIcon(IconRegistry.from_name('fa5s.cat'))
        self.buttonGroup.buttonClicked.connect(self._structureChanged)
        self._structure: Optional[StoryStructure] = None
        self._structureChanged()

    def structure(self) -> Optional[StoryStructure]:
        return self._structure

    @staticmethod
    def display(novel: Novel) -> Optional[StoryStructure]:
        dialog = StoryStructureSelectorDialog(novel)

        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return dialog.structure()

        return None

    def _structureChanged(self):
        if self.btnThreeAct.isChecked():
            self._structure = three_act_structure
            self.stackedWidget.setCurrentWidget(self.pageThreeAct)
            if self.pageThreeAct.layout().count() == 0:
                self.pageThreeAct.layout().addWidget(_ThreeActStructureEditorWidget(self._novel, self))
        elif self.btnSaveTheCat.isChecked():
            self._structure = save_the_cat
            self.stackedWidget.setCurrentWidget(self.pageSaveTheCat)


class StoryStructureEditor(QWidget, Ui_StoryStructureSettings):
    def __init__(self, parent=None):
        super(StoryStructureEditor, self).__init__(parent)
        self.setupUi(self)
        flow(self.wdgTemplates)

        self.btnTemplateEditor.setIcon(IconRegistry.plus_edit_icon())
        self.btnLinkCharacter.setIcon(IconRegistry.character_icon())
        self.btnLinkCharacter.setStyleSheet('''
            QPushButton {
                border: 2px dotted grey;
                border-radius: 6px;
                font: italic;
            }
            QPushButton:hover {
                border: 2px dotted darkBlue;
            }
        ''')
        self.btnTemplateEditor.clicked.connect(self._selectTemplateStructure)
        self.wdgCharacterLink: Optional[StoryStructureCharacterLinkWidget] = None
        self.btnGroupStructure = QButtonGroup()
        self.btnGroupStructure.setExclusive(True)

        self.__initWdgPReview()

        self.novel: Optional[Novel] = None
        self.beats.installEventFilter(self)
        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Leave:
            self.wdgPreview.unhighlightBeats()

        return super(StoryStructureEditor, self).eventFilter(watched, event)

    def setNovel(self, novel: Novel):
        self.novel = novel
        self.wdgCharacterLink = StoryStructureCharacterLinkWidget(self.novel)
        self.wdgCharacterLink.linkCharacter.connect(self._linkCharacter)
        self.wdgCharacterLink.unlinkCharacter.connect(self._unlinkCharacter)
        btn_popup(self.btnLinkCharacter, self.wdgCharacterLink)
        for structure in self.novel.story_structures:
            self._addStructure(structure)

    def _addStructure(self, structure: StoryStructure):
        btn = _StoryStructureButton(structure, self.novel)
        btn.toggled.connect(partial(self._activeStructureToggled, structure))
        btn.clicked.connect(partial(self._activeStructureClicked, structure))
        self.btnGroupStructure.addButton(btn)
        self.wdgTemplates.layout().addWidget(btn)
        if structure.active:
            btn.setChecked(True)

    def _removeStructure(self, structure: StoryStructure):
        to_be_removed = []
        activate_new = False
        for btn in self.btnGroupStructure.buttons():
            if btn.structure().id == structure.id and btn.structure().character_id == structure.character_id:
                to_be_removed.append(btn)
                if btn.isChecked():
                    activate_new = True

        for btn in to_be_removed:
            self.btnGroupStructure.removeButton(btn)
            self.wdgTemplates.layout().removeWidget(btn)
            gc(btn)
        if activate_new and self.btnGroupStructure.buttons():
            self.btnGroupStructure.buttons()[0].setChecked(True)
            emit_event(NovelStoryStructureUpdated(self))

    def _linkCharacter(self, character: Character):
        new_structure = copy.deepcopy(self.novel.active_story_structure)
        new_structure.set_character(character)
        self.novel.story_structures.append(new_structure)
        self._addStructure(new_structure)
        self.repo.update_novel(self.novel)
        emit_event(NovelStoryStructureUpdated(self))

    def _unlinkCharacter(self, character: Character):
        active_structure_id = self.novel.active_story_structure.id
        matched_structures = [x for x in self.novel.story_structures if
                              x.id == active_structure_id and x.character_id == character.id]
        if matched_structures:
            for st in matched_structures:
                self.novel.story_structures.remove(st)
                self._removeStructure(st)

    def _selectTemplateStructure(self):
        structure: Optional[StoryStructure] = StoryStructureSelectorDialog.display(self.novel)
        if structure:
            self.novel.story_structures.append(structure)
            self._addStructure(structure)

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
            self.__initWdgPReview()
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

    def __initWdgPReview(self):
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

    # def _structureSelectionChanged(self, structure: StoryStructure, toggled: bool):
    #     if toggled:
    #         self.novel.story_structures.append(structure)
    #         self._addStructure(structure)
    #     else:
    #         matched_structures = [x for x in self.novel.story_structures if x.id == structure.id]
    #         if matched_structures:
    #             for st in matched_structures:
    #                 self.novel.story_structures.remove(st)
    #         self._removeStructure(structure)
    #
    #     self.repo.update_novel(self.novel)


class TagLabelsEditor(LabelsEditorWidget):

    def __init__(self, novel: Novel, tagType: TagType, tags: List[Tag], parent=None):
        self.novel = novel
        self.tagType = tagType
        self.tags = tags
        super(TagLabelsEditor, self).__init__(checkable=False, parent=parent)
        self.btnEdit.setIcon(IconRegistry.tag_plus_icon())
        self.editor.model.item_edited.connect(self._updateTags)
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


class ImportedNovelOverview(QWidget, Ui_ImportedNovelOverview):
    def __init__(self, parent=None):
        super(ImportedNovelOverview, self).__init__(parent)
        self.setupUi(self)
        self.btnCharacters.setIcon(IconRegistry.character_icon())
        self.btnLocations.setIcon(IconRegistry.location_icon())
        self.btnScenes.setIcon(IconRegistry.scene_icon())

        link_buttons_to_pages(self.stackedWidget,
                              [(self.btnCharacters, self.pageCharacters), (self.btnLocations, self.pageLocations),
                               (self.btnScenes, self.pageScenes)])

        self._charactersModel: Optional[CharactersTableModel] = None
        self._chaptersModel: Optional[ChaptersTreeModel] = None

    def setNovel(self, novel: Novel):
        self.lblTitle.setText(novel.title)

        if novel.characters:
            self._charactersModel = CharactersTableModel(novel)
            self.lstCharacters.setModel(self._charactersModel)
            self.btnCharacters.setChecked(True)
        else:
            self.btnCharacters.setDisabled(True)

        if novel.scenes:
            self._chaptersModel = ChaptersTreeModel(novel)
            self.treeChapters.setModel(self._chaptersModel)
            self.treeChapters.expandAll()
            self.treeChapters.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.treeChapters.hideColumn(ChaptersTreeModel.ColPlus)
            if not self.btnLocations.isChecked():
                self.btnScenes.setChecked(True)


class PlotWidget(QFrame, Ui_PlotWidget):
    removalRequested = pyqtSignal()

    def __init__(self, novel: Novel, plot: Plot, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        self.plot = plot

        incr_font(self.lineName)
        bold(self.lineName)
        self.lineName.setText(self.plot.text)
        self.lineName.textChanged.connect(self._nameEdited)
        self.textQuestion.setPlainText(self.plot.question)
        self.textQuestion.textChanged.connect(self._questionChanged)

        flow(self.wdgValues)

        for value in self.plot.values:
            self._addValue(value)

        self._btnAddValue = SecondaryActionPushButton(self)
        self._btnAddValue.setText('Attach story value')
        self.wdgValues.layout().addWidget(self._btnAddValue)
        self._btnAddValue.clicked.connect(self._newValue)

        self.installEventFilter(VisibilityToggleEventFilter(target=self.btnRemove, parent=self))

        self._updateIcon()

        iconMenu = QMenu(self.btnPlotIcon)

        colorAction = QWidgetAction(iconMenu)
        colorPicker = ColorPicker(self)
        colorPicker.setFixedSize(300, 150)
        colorPicker.colorPicked.connect(self._colorChanged)
        colorAction.setDefaultWidget(colorPicker)
        colorMenu = QMenu('Color', iconMenu)
        colorMenu.setIcon(IconRegistry.from_name('fa5s.palette'))
        colorMenu.addAction(colorAction)

        iconMenu.addMenu(colorMenu)
        iconMenu.addSeparator()
        iconMenu.addAction(
            action('Change icon', icon=IconRegistry.icons_icon(), slot=self._changeIcon, parent=iconMenu))
        btn_popup_menu(self.btnPlotIcon, iconMenu)

        self.btnRemove.clicked.connect(self.removalRequested.emit)
        self.installEventFilter(self)

        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            self.setStyleSheet(f'''
            .PlotWidget {{
                background-color: #dee2e6;
                border-radius: 6px;
                border-left: 8px solid {self.plot.icon_color};
            }}''')
        elif event.type() == QEvent.Type.Leave:
            self.setStyleSheet(f'.PlotWidget {{border-radius: 6px; border-left: 8px solid {self.plot.icon_color};}}')

        return super(PlotWidget, self).eventFilter(watched, event)

    def _updateIcon(self):
        self.setStyleSheet(f'.PlotWidget {{border-radius: 6px; border-left: 8px solid {self.plot.icon_color};}}')
        if self.plot.icon:
            self.btnPlotIcon.setIcon(IconRegistry.from_name(self.plot.icon, self.plot.icon_color))

    def _nameEdited(self, name: str):
        self.plot.text = name
        self.repo.update_novel(self.novel)

    def _questionChanged(self):
        self.plot.question = self.textQuestion.toPlainText()
        self.repo.update_novel(self.novel)

    def _changeIcon(self):
        result = IconSelectorDialog(self).display(QColor(self.plot.icon_color))
        if result:
            self.plot.icon = result[0]
            self.plot.icon_color = result[1].name()
            self._updateIcon()
            self.repo.update_novel(self.novel)

    def _colorChanged(self, color: QColor):
        self.plot.icon_color = color.name()
        self._updateIcon()
        self.repo.update_novel(self.novel)

    def _newValue(self):
        value = PlotValueEditorDialog().display()
        if value:
            self.plot.values.append(value)
            self.wdgValues.layout().removeWidget(self._btnAddValue)
            self._addValue(value)
            self.wdgValues.layout().addWidget(self._btnAddValue)

            self.repo.update_novel(self.novel)

    def _addValue(self, value: PlotValue):
        label = PlotValueLabel(value, parent=self.wdgValues, removalEnabled=True)
        self.wdgValues.layout().addWidget(label)
        label.removalRequested.connect(partial(self._removeValue, label))

    def _removeValue(self, widget: PlotValueLabel):
        if app_env.test_env():
            self.__destroyValue(widget)
        else:
            anim = qtanim.fade_out(widget, duration=150, hide_if_finished=False)
            anim.finished.connect(partial(self.__destroyValue, widget))

    def __destroyValue(self, widget: PlotValueLabel):
        self.plot.values.remove(widget.value)
        self.repo.update_novel(self.novel)
        self.wdgValues.layout().removeWidget(widget)
        gc(widget)


class PlotEditor(QWidget, Ui_PlotEditor):
    def __init__(self, novel: Novel, parent=None):
        super(PlotEditor, self).__init__(parent)
        self.setupUi(self)
        self.novel = novel
        for plot in self.novel.plots:
            self._addPlotWidget(plot)

        italic(self.btnAdd)
        self.btnAdd.setIcon(IconRegistry.plus_icon('grey'))
        menu = QMenu(self.btnAdd)
        menu.addAction(IconRegistry.cause_and_effect_icon(), 'Main plot', lambda: self.newPlot(PlotType.Main))
        menu.addAction(IconRegistry.conflict_self_icon(), 'Internal plot', lambda: self.newPlot(PlotType.Internal))
        menu.addAction(IconRegistry.subplot_icon(), 'Subplot', lambda: self.newPlot(PlotType.Subplot))
        btn_popup_menu(self.btnAdd, menu)

        self.repo = RepositoryPersistenceManager.instance()

    def _addPlotWidget(self, plot: Plot) -> PlotWidget:
        widget = PlotWidget(self.novel, plot)
        margins(widget, left=15)
        widget.removalRequested.connect(partial(self._remove, widget))
        self.scrollAreaWidgetContents.layout().insertWidget(self.scrollAreaWidgetContents.layout().count() - 2, widget)

        return widget

    def newPlot(self, plot_type: PlotType):
        if plot_type == PlotType.Internal:
            name = 'Internal plot'
            icon = 'mdi.mirror'
        elif plot_type == PlotType.Subplot:
            name = 'Subplot'
            icon = 'mdi.source-branch'
        else:
            name = 'Main plot'
            icon = 'mdi.ray-start-arrow'
        plot = Plot(name, plot_type=plot_type, icon=icon)
        self.novel.plots.append(plot)
        plot.icon_color = STORY_LINE_COLOR_CODES[(len(self.novel.plots) - 1) % len(STORY_LINE_COLOR_CODES)]
        widget = self._addPlotWidget(plot)
        widget.lineName.setFocus()

        self.repo.update_novel(self.novel)

    def _remove(self, widget: PlotWidget):
        if ask_confirmation(f'Are you sure you want to delete the plot {widget.plot.text}?'):
            if app_env.test_env():
                self.__destroy(widget)
            else:
                anim = qtanim.fade_out(widget, duration=150)
                anim.finished.connect(partial(self.__destroy, widget))

    def __destroy(self, widget: PlotWidget):
        delete_plot(self.novel, widget.plot)

        self.scrollAreaWidgetContents.layout().removeWidget(widget)
        gc(widget)
