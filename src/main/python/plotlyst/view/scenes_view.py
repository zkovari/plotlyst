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
from typing import Optional

import qtawesome
from PyQt6.QtCore import Qt, QModelIndex, \
    QPoint
from PyQt6.QtWidgets import QWidget, QHeaderView, QMenu
from overrides import overrides
from qthandy import ask_confirmation, incr_font, translucent, btn_popup, clear_layout, busy, bold

from src.main.python.plotlyst.common import RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import Scene, Novel, Chapter, SceneStage, Event, SceneType
from src.main.python.plotlyst.event.core import emit_event, EventListener
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import SceneChangedEvent, SceneDeletedEvent, NovelStoryStructureUpdated, \
    SceneSelectedEvent, SceneSelectionClearedEvent, ToggleOutlineViewTitle, ActiveSceneStageChanged, \
    ChapterChangedEvent, AvailableSceneStagesChanged
from src.main.python.plotlyst.model.chapters_model import ChaptersTreeModel, SceneNode
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.model.novel import NovelStagesModel
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel, ScenesFilterProxyModel, ScenesStageTableModel
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import PopupMenuBuilder
from src.main.python.plotlyst.view.delegates import ScenesViewDelegate
from src.main.python.plotlyst.view.dialog.items import ItemsEditorDialog
from src.main.python.plotlyst.view.generated.scenes_title_ui import Ui_ScenesTitle
from src.main.python.plotlyst.view.generated.scenes_view_ui import Ui_ScenesView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.scene_editor import SceneEditor
from src.main.python.plotlyst.view.widget.cards import SceneCard
from src.main.python.plotlyst.view.widget.characters import CharactersScenesDistributionWidget
from src.main.python.plotlyst.view.widget.chart import ActDistributionChart
from src.main.python.plotlyst.view.widget.display import ChartView
from src.main.python.plotlyst.view.widget.input import RotatedButtonOrientation
from src.main.python.plotlyst.view.widget.progress import SceneStageProgressCharts
from src.main.python.plotlyst.view.widget.scenes import SceneFilterWidget, SceneStoryStructureWidget, \
    ScenesPreferencesWidget, StoryMap, StoryMapDisplayMode
from src.main.python.plotlyst.view.widget.scenes import StoryLinesMapWidget


class ScenesTitle(QWidget, Ui_ScenesTitle, EventListener):

    def __init__(self, novel: Novel, parent=None):
        super(ScenesTitle, self).__init__(parent)
        self.novel = novel
        self.setupUi(self)
        self.btnScenes.setIcon(IconRegistry.scene_icon())
        incr_font(self.lblTitle)
        bold(self.lblTitle)
        self.btnScene.setIcon(IconRegistry.action_scene_icon())
        self.btnSequel.setIcon(IconRegistry.reaction_scene_icon())
        translucent(self.btnScene, 0.6)
        translucent(self.btnSequel, 0.6)

        self._chartDistribution = ActDistributionChart()
        self._chartDistributionView = ChartView()
        self._chartDistributionView.setMaximumSize(356, 356)
        self._chartDistributionView.setChart(self._chartDistribution)

        btn_popup(self.btnCount, self._chartDistributionView)
        self.refresh()

        event_dispatcher.register(self, SceneChangedEvent)
        event_dispatcher.register(self, SceneDeletedEvent)

    @overrides
    def event_received(self, event: Event):
        self.refresh()

    def refresh(self):
        self.btnCount.setText(f'#{len(self.novel.scenes)}')
        self.btnScene.setText(f'{len([x for x in self.novel.scenes if x.type == SceneType.ACTION])}')
        self.btnSequel.setText(f'{len([x for x in self.novel.scenes if x.type == SceneType.REACTION])}')

        self._chartDistribution.refresh(self.novel)


class ScenesOutlineView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [NovelStoryStructureUpdated, SceneChangedEvent, ChapterChangedEvent, SceneDeletedEvent])
        self.ui = Ui_ScenesView()
        self.ui.setupUi(self.widget)

        self.title = ScenesTitle(self.novel)

        self.editor: Optional[SceneEditor] = None
        self.storymap_view: Optional[StoryLinesMapWidget] = None
        self.stagesModel: Optional[ScenesStageTableModel] = None
        self.stagesProgress: Optional[SceneStageProgressCharts] = None
        self.characters_distribution: Optional[CharactersScenesDistributionWidget] = None

        self.tblModel = ScenesTableModel(novel)
        self._default_columns = [ScenesTableModel.ColTitle, ScenesTableModel.ColPov, ScenesTableModel.ColType,
                                 ScenesTableModel.ColCharacters,
                                 ScenesTableModel.ColSynopsis]
        self._proxy = ScenesFilterProxyModel()
        self._proxy.setSourceModel(self.tblModel)
        self._proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.tblScenes.setModel(self._proxy)
        self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColTitle,
                                                                  QHeaderView.ResizeMode.Fixed)
        self.ui.tblScenes.horizontalHeader().setFixedHeight(30)
        self.ui.tblScenes.verticalHeader().setStyleSheet(
            '''QHeaderView::section {background-color: white; border: 0px; color: black; font-size: 14px;}
               QHeaderView {background-color: white;}''')
        self.ui.tblScenes.verticalHeader().setFixedWidth(40)
        self.ui.tblScenes.verticalHeader().setVisible(True)
        self.tblModel.orderChanged.connect(self._on_scene_moved)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColTitle, 250)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColCharacters, 170)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColType, 55)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColPov, 60)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColSynopsis, 400)
        self.ui.tblScenes.setItemDelegate(ScenesViewDelegate())
        self.ui.tblScenes.hideColumn(ScenesTableModel.ColTime)

        self.widget.setStyleSheet(f'#cards {{background: {RELAXED_WHITE_COLOR};}}')

        self.ui.splitterLeft.setSizes([100, 500])

        self.chaptersModel = ChaptersTreeModel(self.novel)
        self.ui.treeChapters.setModel(self.chaptersModel)
        self.ui.treeChapters.selectionModel().selectionChanged.connect(self._on_chapter_selected)

        self.ui.treeChapters.doubleClicked.connect(self._on_edit)

        self.ui.wgtChapters.setVisible(self.ui.btnChaptersToggle.isChecked())
        self.ui.btnChaptersToggle.setIcon(IconRegistry.chapter_icon())
        self.ui.btnChaptersToggle.setChecked(self.novel.prefs.panels.scene_chapters_sidebar_toggled)
        self.ui.btnChaptersToggle.toggled.connect(self._hide_chapters_toggled)
        self._hide_chapters_toggled(self.ui.btnChaptersToggle.isChecked())

        self.ui.btnAct1.setIcon(IconRegistry.act_one_icon(color='grey'))
        self.ui.btnAct2.setIcon(IconRegistry.act_two_icon(color='grey'))
        self.ui.btnAct3.setIcon(IconRegistry.act_three_icon(color='grey'))
        self.ui.btnAct1.toggled.connect(partial(self._proxy.setActsFilter, 1))
        self.ui.btnAct2.toggled.connect(partial(self._proxy.setActsFilter, 2))
        self.ui.btnAct3.toggled.connect(partial(self._proxy.setActsFilter, 3))

        self.ui.btnCardsView.setIcon(IconRegistry.cards_icon())
        self.ui.btnTableView.setIcon(IconRegistry.table_icon())
        self.ui.btnStoryStructure.setIcon(IconRegistry.story_structure_icon(color_on='darkBlue'))
        self.ui.btnStatusView.setIcon(IconRegistry.progress_check_icon('black'))
        self.ui.btnCharactersDistributionView.setIcon(qtawesome.icon('fa5s.chess-board'))
        self.ui.btnStorymap.setIcon(IconRegistry.from_name('mdi.transit-connection-horizontal', color_on='darkBlue'))

        self.ui.rbDots.setIcon(IconRegistry.from_name('fa5s.circle'))
        self.ui.rbTitles.setIcon(IconRegistry.from_name('ei.text-width'))
        self.ui.rbDetailed.setIcon(IconRegistry.from_name('mdi.card-text-outline'))
        self.ui.wdgOrientation.setHidden(True)
        self.ui.rbHorizontal.setIcon(IconRegistry.from_name('fa5s.grip-lines'))
        self.ui.rbVertical.setIcon(IconRegistry.from_name('fa5s.grip-lines-vertical'))

        self.ui.btnStageCustomize.setIcon(IconRegistry.cog_icon())
        self.ui.btnStageCustomize.clicked.connect(self._customize_stages)

        self.selected_card: Optional[SceneCard] = None
        self.ui.btnAct1.toggled.connect(self._update_cards)
        self.ui.btnAct2.toggled.connect(self._update_cards)
        self.ui.btnAct3.toggled.connect(self._update_cards)
        self.ui.cards.selectionCleared.connect(lambda: self._enable_action_buttons(False))

        self.ui.btnGroupViews.buttonToggled.connect(self._switch_view)
        self.ui.btnCardsView.setChecked(True)

        self.ui.wdgStoryStructureParent.setHidden(True)
        self.ui.wdgStoryStructure.setBeatCursor(Qt.CursorShape.ArrowCursor)
        self.ui.wdgStoryStructure.setNovel(self.novel)
        self.ui.wdgStoryStructure.setActsClickable(False)

        self.ui.btnFilter.setIcon(IconRegistry.filter_icon())
        self.ui.btnPreferences.setIcon(IconRegistry.preferences_icon())
        self.prefs_widget = ScenesPreferencesWidget()
        btn_popup(self.ui.btnPreferences, self.prefs_widget)
        self.prefs_widget.sliderCards.valueChanged.connect(self.ui.cards.setCardsWidth)
        self.ui.cards.setCardsWidth(self.prefs_widget.sliderCards.value())

        self._scene_filter = SceneFilterWidget(self.novel)
        btn_popup(self.ui.btnFilter, self._scene_filter)
        self._scene_filter.povFilter.characterToggled.connect(self._proxy.setCharacterFilter)
        self._scene_filter.povFilter.characterToggled.connect(self._update_cards)

        self._update_cards()

        self.ui.tblScenes.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tblScenes.customContextMenuRequested.connect(self._on_custom_menu_requested)

        self.ui.tblScenes.selectionModel().selectionChanged.connect(self._on_scene_selected)
        self.ui.tblScenes.doubleClicked.connect(self.ui.btnEdit.click)

        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.clicked.connect(self._new_scene)
        self.ui.btnDelete.setIcon(IconRegistry.trash_can_icon(color='white'))
        self.ui.btnDelete.clicked.connect(self._on_delete)

        self.ui.cards.swapped.connect(self._scenes_swapped)

    @overrides
    def refresh(self):
        self.tblModel.modelReset.emit()
        self.chaptersModel.update()
        self.chaptersModel.modelReset.emit()
        self.ui.btnEdit.setDisabled(True)
        self.ui.btnDelete.setDisabled(True)

        if self.ui.wdgStoryStructure.novel is not None:
            clear_layout(self.ui.wdgStoryStructureParent)
            self.ui.wdgStoryStructure = SceneStoryStructureWidget(self.ui.wdgStoryStructureParent)
            self.ui.wdgStoryStructure.setBeatCursor(Qt.CursorShape.ArrowCursor)
            self.ui.wdgStoryStructureParent.layout().addWidget(self.ui.wdgStoryStructure)
        self.ui.wdgStoryStructure.setNovel(self.novel)
        self.ui.wdgStoryStructure.setActsClickable(False)

        if self.stagesModel:
            self.stagesModel.modelReset.emit()
        if self.stagesProgress:
            self.stagesProgress.refresh()
        if self.characters_distribution:
            self.characters_distribution.refresh()

        self._update_cards()

    @overrides
    def can_show_title(self) -> bool:
        return self.ui.stackedWidget.currentWidget() is self.ui.pageView

    def _on_scene_selected(self):
        indexes = self.ui.tblScenes.selectedIndexes()
        selection = len(indexes) > 0
        self.ui.btnDelete.setEnabled(selection)
        self.ui.btnEdit.setEnabled(selection)
        if selection:
            self.ui.treeChapters.clearSelection()
            emit_event(
                SceneSelectedEvent(self, indexes[0].data(ScenesTableModel.SceneRole)))

    def _on_chapter_selected(self):
        indexes = self.ui.treeChapters.selectedIndexes()
        if not indexes:
            return

        self.ui.tblScenes.clearSelection()
        if self.selected_card:
            self.selected_card.clearSelection()
            self.selected_card = None

        self.ui.btnDelete.setEnabled(True)
        node = indexes[0].data(ChaptersTreeModel.NodeRole)
        self.ui.btnEdit.setEnabled(isinstance(node, SceneNode))

    def _hide_chapters_toggled(self, toggled: bool):
        if toggled:
            menu = QMenu(self.ui.btnNew)
            menu.addAction(IconRegistry.scene_icon(), 'Add scene', self._new_scene)
            menu.addAction(IconRegistry.chapter_icon(), 'Add chapter', self.ui.treeChapters.insertChapter)
            self.ui.btnNew.setMenu(menu)
        else:
            self.ui.btnNew.setMenu(None)

        if self.novel.prefs.panels.scene_chapters_sidebar_toggled != toggled:
            self.novel.prefs.panels.scene_chapters_sidebar_toggled = toggled
            self.repo.update_novel(self.novel)

    def _on_edit(self):
        scene: Optional[Scene] = self._selected_scene()
        if scene:
            self.editor = SceneEditor(self.novel, scene)
            self._switch_to_editor()

    def _selected_scene(self) -> Optional[Scene]:
        if self.ui.btnCardsView.isChecked() and self.selected_card:
            return self.selected_card.scene
        elif self.ui.treeChapters.selectionModel().selectedIndexes():
            index = self.ui.treeChapters.selectionModel().selectedIndexes()[0]
            node = index.data(ChaptersTreeModel.NodeRole)
            if isinstance(node, SceneNode):
                return node.scene
            return None
        else:
            indexes = None
            if self.ui.btnTableView.isChecked():
                indexes = self.ui.tblScenes.selectedIndexes()

            if indexes:
                return indexes[0].data(role=ScenesTableModel.SceneRole)
            else:
                return None

    @busy
    def _switch_to_editor(self):
        emit_event(ToggleOutlineViewTitle(self, visible=False))
        self.ui.pageEditor.layout().addWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEditor)

        self.editor.ui.btnClose.clicked.connect(self._on_close_editor)

    def _on_close_editor(self):
        self.ui.pageEditor.layout().removeWidget(self.editor.widget)
        if self.editor.scene.pov and self.editor.scene.pov not in self._scene_filter.povFilter.characters():
            self._scene_filter.povFilter.addCharacter(self.editor.scene.pov)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageView)
        self.editor.widget.deleteLater()
        self.editor = None

        emit_event(SceneChangedEvent(self))
        emit_event(ToggleOutlineViewTitle(self, visible=True))
        self.refresh()

    def _new_scene(self):
        self.editor = SceneEditor(self.novel)
        self._switch_to_editor()

    def _update_cards(self):
        def custom_menu(card: SceneCard, pos: QPoint):
            builder = PopupMenuBuilder.from_widget_position(card, pos)
            builder.add_action('Edit', IconRegistry.edit_icon(), self._on_edit)
            builder.add_action('Insert new scene', IconRegistry.plus_icon('black'),
                               partial(self._insert_scene_after, card.scene))
            builder.add_separator()
            builder.add_action('Delete', IconRegistry.trash_can_icon(), self.ui.btnDelete.click)
            builder.popup()

        self.selected_card = None
        self.ui.cards.clear()

        acts_filter = {1: self.ui.btnAct1.isChecked(), 2: self.ui.btnAct2.isChecked(), 3: self.ui.btnAct3.isChecked()}
        active_povs = self._scene_filter.povFilter.characters(all=False)
        for scene in self.novel.scenes:
            if not acts_filter[acts_registry.act(scene)]:
                continue
            if scene.pov and scene.pov not in active_povs:
                continue
            card = SceneCard(scene, self.novel, self.ui.cards)
            self.ui.cards.addCard(card)
            card.selected.connect(self._card_selected)
            card.doubleClicked.connect(self._on_edit)
            card.cursorEntered.connect(partial(self.ui.wdgStoryStructure.highlightScene, card.scene))
            card.customContextMenuRequested.connect(partial(custom_menu, card))

    def _card_selected(self, card: SceneCard):
        if self.selected_card and self.selected_card is not card:
            self.selected_card.clearSelection()
        self.selected_card = card
        self._enable_action_buttons(True)
        emit_event(SceneSelectedEvent(self, card.scene))

    def _enable_action_buttons(self, enabled: bool):
        self.ui.btnDelete.setEnabled(enabled)
        self.ui.btnEdit.setEnabled(enabled)

    def _switch_view(self):
        height = 50
        relax_colors = False
        columns = self._default_columns

        if self.ui.btnStatusView.isChecked():
            self.ui.stackScenes.setCurrentWidget(self.ui.pageStages)
            self.ui.tblScenes.clearSelection()
            if not self.stagesModel:
                self._init_stages_view()
        elif self.ui.btnCardsView.isChecked():
            self.ui.stackScenes.setCurrentWidget(self.ui.pageCards)
            self.ui.tblScenes.clearSelection()
        elif self.ui.btnStorymap.isChecked():
            self.ui.stackScenes.setCurrentWidget(self.ui.pageStorymap)
            self.ui.tblScenes.clearSelection()
            self.ui.tblSceneStages.clearSelection()
            if not self.storymap_view:
                self.storymap_view = StoryMap()
                self.ui.scrollAreaStoryMap.layout().addWidget(self.storymap_view)
                self.ui.rbDots.clicked.connect(lambda: self.storymap_view.setMode(StoryMapDisplayMode.DOTS))
                self.ui.rbTitles.clicked.connect(lambda: self.storymap_view.setMode(StoryMapDisplayMode.TITLE))
                self.ui.rbDetailed.clicked.connect(lambda: self.storymap_view.setMode(StoryMapDisplayMode.DETAILED))
                self.ui.rbHorizontal.clicked.connect(
                    lambda: self.storymap_view.setOrientation(Qt.Orientation.Horizontal))
                self.ui.rbVertical.clicked.connect(lambda: self.storymap_view.setOrientation(Qt.Orientation.Vertical))
                self.ui.btnAct1.toggled.connect(partial(self.storymap_view.setActsFilter, 1))
                self.ui.btnAct2.toggled.connect(partial(self.storymap_view.setActsFilter, 2))
                self.ui.btnAct3.toggled.connect(partial(self.storymap_view.setActsFilter, 3))
                self.storymap_view.setActsFilter(1, self.ui.btnAct1.isChecked())
                self.storymap_view.setActsFilter(2, self.ui.btnAct2.isChecked())
                self.storymap_view.setActsFilter(3, self.ui.btnAct3.isChecked())
                self.storymap_view.sceneSelected.connect(self.ui.wdgStoryStructure.highlightScene)
                self.storymap_view.setNovel(self.novel)
        elif self.ui.btnCharactersDistributionView.isChecked():
            self.ui.stackScenes.setCurrentWidget(self.ui.pageCharactersDistribution)
            self.ui.tblScenes.clearSelection()
            self.ui.tblSceneStages.clearSelection()
            if not self.characters_distribution:
                self.characters_distribution = CharactersScenesDistributionWidget(self.novel)
                self.ui.pageCharactersDistribution.layout().addWidget(self.characters_distribution)
                self.ui.btnAct1.toggled.connect(partial(self.characters_distribution.setActsFilter, 1))
                self.ui.btnAct2.toggled.connect(partial(self.characters_distribution.setActsFilter, 2))
                self.ui.btnAct3.toggled.connect(partial(self.characters_distribution.setActsFilter, 3))
                self.characters_distribution.setActsFilter(1, self.ui.btnAct1.isChecked())
                self.characters_distribution.setActsFilter(2, self.ui.btnAct2.isChecked())
                self.characters_distribution.setActsFilter(3, self.ui.btnAct3.isChecked())
        else:
            self.ui.stackScenes.setCurrentWidget(self.ui.pageDefault)
            self.ui.tblSceneStages.clearSelection()

        self.tblModel.setRelaxColors(relax_colors)
        for col in range(self.tblModel.columnCount()):
            if col in columns:
                self.ui.tblScenes.showColumn(col)
                continue
            self.ui.tblScenes.hideColumn(col)
        self.ui.tblScenes.verticalHeader().setDefaultSectionSize(height)

        emit_event(SceneSelectionClearedEvent(self))

    def _customize_stages(self):
        diag = ItemsEditorDialog(NovelStagesModel(copy.deepcopy(self.novel.stages)))
        diag.wdgItemsEditor.tableView.setColumnHidden(SelectionItemsModel.ColIcon, True)
        diag.wdgItemsEditor.setRemoveAllEnabled(False)
        diag.wdgItemsEditor.setInsertionEnabled(True)
        items = diag.display()
        if items:
            self.novel.stages.clear()
            self.novel.stages.extend(items)

            for scene in self.novel.scenes:
                if scene.stage not in self.novel.stages:
                    scene.stage = None
                    self.repo.update_scene(scene)

            self.repo.update_novel(self.novel)
            self._init_stages_view()
            emit_event(AvailableSceneStagesChanged(self))

    def _init_stages_view(self):
        def change_stage(stage: SceneStage):
            self.stagesProgress.setStage(stage)
            self.ui.btnStageSelector.setText(stage.text)
            self.stagesModel.setHighlightedStage(stage)
            self.novel.prefs.active_stage_id = stage.id
            self.repo.update_novel(self.novel)
            emit_event(ActiveSceneStageChanged(self, stage))

        def header_clicked(col: int):
            if col > 1:
                stage = self.novel.stages[col - 2]
                change_stage(stage)

        if self.stagesModel:
            self.stagesModel.modelReset.emit()
        else:
            self.stagesModel = ScenesStageTableModel(self.novel)
            self._stages_proxy = ScenesFilterProxyModel()
            self._stages_proxy.setSourceModel(self.stagesModel)
            self._stages_proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._stages_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.ui.tblSceneStages.setModel(self._stages_proxy)
            self.ui.btnAct1.toggled.connect(partial(self._stages_proxy.setActsFilter, 1))
            self.ui.btnAct2.toggled.connect(partial(self._stages_proxy.setActsFilter, 2))
            self.ui.btnAct3.toggled.connect(partial(self._stages_proxy.setActsFilter, 3))
            self._stages_proxy.setActsFilter(1, self.ui.btnAct1.isChecked())
            self._stages_proxy.setActsFilter(2, self.ui.btnAct2.isChecked())
            self._stages_proxy.setActsFilter(3, self.ui.btnAct3.isChecked())
            self.ui.tblSceneStages.verticalHeader().setStyleSheet(
                '''QHeaderView::section {background-color: white; border: 0px; color: black; font-size: 14px;}
                   QHeaderView {background-color: white;}''')
            self.ui.tblSceneStages.verticalHeader().setFixedWidth(40)
            self.ui.tblSceneStages.horizontalHeader().sectionClicked.connect(header_clicked)
            self.ui.tblSceneStages.setColumnWidth(ScenesStageTableModel.ColTitle, 250)

        for col in range(1, self.stagesModel.columnCount()):
            self.ui.tblSceneStages.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            w = self.ui.tblSceneStages.horizontalHeader().sectionSize(col)
            self.ui.tblSceneStages.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.ui.tblSceneStages.setColumnWidth(col, w + 10)

        if not self.stagesProgress:
            self.stagesProgress = SceneStageProgressCharts(self.novel)

            self.ui.tblSceneStages.clicked.connect(
                lambda x: self.stagesModel.changeStage(self._stages_proxy.mapToSource(x)))

            self.ui.btnStageSelector.setOrientation(RotatedButtonOrientation.VerticalBottomToTop)
            self.ui.btnStageSelector.setIcon(IconRegistry.progress_check_icon())

        menu = QMenu(self.ui.btnStageSelector)
        for stage in self.novel.stages:
            menu.addAction(stage.text, partial(change_stage, stage))
        menu.addSeparator()
        menu.addAction(IconRegistry.cog_icon(), 'Customize', self._customize_stages)
        self.ui.btnStageSelector.setMenu(menu)
        if not self.novel.prefs.active_stage_id:
            self.novel.prefs.active_stage_id = self.stagesProgress.stage().id
            self.repo.update_novel(self.novel)
        self.ui.btnStageSelector.setText(self.stagesProgress.stage().text)
        self.stagesModel.setHighlightedStage(self.stagesProgress.stage())

        if self.novel.scenes:
            self.stagesProgress.refresh()
            if not self.ui.wdgProgressCharts.layout().count():
                for i, chartview in enumerate(self.stagesProgress.charts()):
                    self.ui.wdgProgressCharts.layout().insertWidget(i, chartview)

    def _on_custom_menu_requested(self, pos: QPoint):
        def toggle_wip(scene: Scene):
            scene.wip = not scene.wip
            self.repo.update_scene(scene)
            self.refresh()

        index: QModelIndex = self.ui.tblScenes.indexAt(pos)
        scene: Scene = index.data(ScenesTableModel.SceneRole)

        builder = PopupMenuBuilder.from_widget_position(self.ui.tblScenes, pos)
        builder.add_action('Toggle WIP status', IconRegistry.wip_icon(), lambda: toggle_wip(scene))
        builder.add_action('Insert new scene', IconRegistry.plus_icon(),
                           lambda: self._insert_scene_after(index.data(ScenesTableModel.SceneRole)))
        builder.add_separator()
        builder.add_action('Delete', IconRegistry.trash_can_icon(), self.ui.btnDelete.click)

        builder.popup()

    def _insert_scene_after(self, scene: Scene, chapter: Optional[Chapter] = None):
        new_scene = self.novel.insert_scene_after(scene, chapter)
        self.repo.insert_scene(self.novel, new_scene)
        emit_event(SceneChangedEvent(self))

        self.refresh()
        self.editor = SceneEditor(self.novel, new_scene)
        self._switch_to_editor()

    def _on_delete(self):
        scene: Optional[Scene] = self._selected_scene()
        if scene and ask_confirmation(f'Are you sure you want to delete scene {scene.title_or_index(self.novel)}?'):
            self.novel.scenes.remove(scene)
            self.repo.delete_scene(self.novel, scene)
            self.refresh()
            emit_event(SceneDeletedEvent(self))
        elif not scene:
            if not self.ui.treeChapters.selectedChapter():
                return
            index = self.ui.treeChapters.selectionModel().selectedIndexes()[0]
            if ask_confirmation(f'Are you sure you want to delete "{index.data()}"? (scenes will remain)'):
                self.chaptersModel.removeChapter(index)
                emit_event(ChapterChangedEvent(self))

    def _scenes_swapped(self, removed: SceneCard, moved_to: SceneCard):
        self.novel.scenes.remove(removed.scene)
        pos = self.novel.scenes.index(moved_to.scene)
        self.novel.scenes.insert(pos, removed.scene)

        emit_event(SceneChangedEvent(self))
        self.refresh()
        self.repo.update_novel(self.novel)

    def _on_scene_moved(self):
        self.repo.update_novel(self.novel)
        self.refresh()
