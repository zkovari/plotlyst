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
from functools import partial
from typing import Optional, List

import qtawesome
from PyQt5.QtCore import pyqtSignal, Qt, QModelIndex, \
    QPoint
from PyQt5.QtWidgets import QWidget, QHeaderView, QToolButton, QMenu, QAction
from overrides import overrides

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Scene, Novel, Character
from src.main.python.plotlyst.event.core import emit_event
from src.main.python.plotlyst.events import SceneChangedEvent, SceneDeletedEvent, NovelStoryStructureUpdated
from src.main.python.plotlyst.model.chapters_model import ChaptersTreeModel
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel, ScenesFilterProxyModel, ScenesStageTableModel
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import EditorCommand, ask_confirmation, EditorCommandType
from src.main.python.plotlyst.view.delegates import ScenesViewDelegate
from src.main.python.plotlyst.view.generated.scenes_view_ui import Ui_ScenesView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import FlowLayout
from src.main.python.plotlyst.view.scene_editor import SceneEditor
from src.main.python.plotlyst.view.timeline_view import TimelineView
from src.main.python.plotlyst.view.widget.cards import SceneCard
from src.main.python.plotlyst.view.widget.characters import CharactersScenesDistributionWidget
from src.main.python.plotlyst.view.widget.progress import SceneStageProgressCharts


class ScenesOutlineView(AbstractNovelView):
    commands_sent = pyqtSignal(QWidget, list)

    def __init__(self, novel: Novel):
        super().__init__(novel, [NovelStoryStructureUpdated])
        self.ui = Ui_ScenesView()
        self.ui.setupUi(self.widget)

        self.editor: Optional[SceneEditor] = None
        self.timeline_view: Optional[TimelineView] = None
        self.stagesModel: Optional[ScenesStageTableModel] = None
        self.stagesProgress: Optional[SceneStageProgressCharts] = None
        self.characters_distribution: Optional[CharactersScenesDistributionWidget] = None

        self.tblModel = ScenesTableModel(novel)
        self._default_columns = [ScenesTableModel.ColTitle, ScenesTableModel.ColPov, ScenesTableModel.ColType,
                                 ScenesTableModel.ColCharacters,
                                 ScenesTableModel.ColSynopsis]
        self._actions_view_columns = [ScenesTableModel.ColPov, ScenesTableModel.ColTitle,
                                      ScenesTableModel.ColBeginning,
                                      ScenesTableModel.ColMiddle, ScenesTableModel.ColEnd]
        self._proxy = ScenesFilterProxyModel()
        self._proxy.setSourceModel(self.tblModel)
        self._proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.ui.tblScenes.setModel(self._proxy)
        self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColTitle, QHeaderView.Fixed)
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

        self.ui.splitterLeft.setSizes([70, 500])

        self.chaptersModel = ChaptersTreeModel(self.novel)
        self.ui.treeChapters.setModel(self.chaptersModel)
        self.ui.treeChapters.expandAll()
        self.chaptersModel.orderChanged.connect(self._on_scene_moved)
        self.chaptersModel.modelReset.connect(self.ui.treeChapters.expandAll)
        self.ui.treeChapters.setColumnWidth(1, 20)
        self.ui.treeChapters.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.treeChapters.selectionModel().selectionChanged.connect(self._on_chapter_selected)
        self.ui.btnChaptersToggle.toggled.connect(self._hide_chapters_toggled)
        self.ui.btnChaptersToggle.setChecked(True)

        self.ui.btnAct1.setIcon(IconRegistry.act_one_icon())
        self.ui.btnAct2.setIcon(IconRegistry.act_two_icon())
        self.ui.btnAct3.setIcon(IconRegistry.act_three_icon())
        self.ui.btnAct1.toggled.connect(partial(self._proxy.setActsFilter, 1))
        self.ui.btnAct2.toggled.connect(partial(self._proxy.setActsFilter, 2))
        self.ui.btnAct3.toggled.connect(partial(self._proxy.setActsFilter, 3))

        self.ui.btnCardsView.setIcon(IconRegistry.cards_icon())
        self.ui.btnTableView.setIcon(IconRegistry.table_icon())
        self.ui.btnActionsView.setIcon(IconRegistry.action_scene_icon())
        self.ui.btnStatusView.setIcon(IconRegistry.progress_check_icon())
        self.ui.btnCharactersDistributionView.setIcon(qtawesome.icon('fa5s.chess-board'))
        self.ui.btnTimelineView.setIcon(IconRegistry.timeline_icon())

        self._cards_layout = FlowLayout(spacing=9)
        self.ui.cards.setLayout(self._cards_layout)
        self.scene_cards: List[SceneCard] = []
        self.selected_card: Optional[SceneCard] = None
        self._update_cards()

        self.ui.btnGroupViews.buttonToggled.connect(self._switch_view)
        self.ui.btnCardsView.setChecked(True)

        self.ui.btnFilter.setPopupMode(QToolButton.InstantPopup)
        self.ui.btnFilter.setIcon(IconRegistry.filter_icon())

        for pov in self.novel.pov_characters():
            self._add_pov_filter_action(pov)

        self.ui.tblScenes.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tblScenes.customContextMenuRequested.connect(self._on_custom_menu_requested)

        self.ui.tblScenes.selectionModel().selectionChanged.connect(self._on_scene_selected)
        self.ui.tblScenes.doubleClicked.connect(self.ui.btnEdit.click)

        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.clicked.connect(self._on_new)
        self.ui.btnDelete.setIcon(IconRegistry.trash_can_icon(color='white'))
        self.ui.btnDelete.clicked.connect(self._on_delete)

    def _add_pov_filter_action(self, pov: Character):
        action = QAction(pov.name, self.ui.btnFilter)
        action.setCheckable(True)
        action.setChecked(True)
        action.triggered.connect(partial(self._proxy.setCharacterFilter, pov))
        self.ui.btnFilter.addAction(action)

    @overrides
    def refresh(self):
        self.tblModel.modelReset.emit()
        self.chaptersModel.update()
        self.chaptersModel.modelReset.emit()
        self.ui.btnEdit.setDisabled(True)
        self.ui.btnDelete.setDisabled(True)

        if self.stagesModel:
            self.stagesModel.modelReset.emit()
        if self.stagesProgress:
            self.stagesProgress.refresh()
        if self.timeline_view:
            self.timeline_view.refresh()
        if self.characters_distribution:
            self.characters_distribution.refresh()

        self._update_cards()

    def _on_scene_selected(self):
        selection = len(self.ui.tblScenes.selectedIndexes()) > 0
        self.ui.btnDelete.setEnabled(selection)
        self.ui.btnEdit.setEnabled(selection)
        if selection:
            self.ui.treeChapters.clearSelection()

    def _on_chapter_selected(self):
        selection = len(self.ui.treeChapters.selectedIndexes()) > 0
        if selection:
            self.ui.tblScenes.clearSelection()

    def _hide_chapters_toggled(self, toggled: bool):
        self.ui.wgtChapters.setHidden(toggled)
        self.ui.btnChaptersToggle.setIcon(IconRegistry.eye_open_icon() if toggled else IconRegistry.eye_closed_icon())
        if toggled:
            self.ui.btnNew.setMenu(None)
        else:
            menu = QMenu(self.ui.btnNew)
            menu.addAction(IconRegistry.scene_icon(), 'Add Scene', self._on_new)
            menu.addAction(IconRegistry.chapter_icon(), 'Add Chapter', self._new_chapter)
            self.ui.btnNew.setMenu(menu)

    def _on_edit(self):
        if self.ui.btnTableView.isChecked():
            indexes = self.ui.tblScenes.selectedIndexes()
            if indexes:
                scene = indexes[0].data(role=ScenesTableModel.SceneRole)
            else:
                return
        elif self.ui.btnCardsView.isChecked():
            scene = self.selected_card.scene
        else:
            return

        self.editor = SceneEditor(self.novel, scene)
        self._switch_to_editor()

    def _switch_to_editor(self):
        self.ui.pageEditor.layout().addWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEditor)

        self.editor.ui.btnClose.clicked.connect(self._on_close_editor)

    def _on_close_editor(self):
        self.ui.pageEditor.layout().removeWidget(self.editor.widget)
        if self.editor.scene.pov and self.editor.scene.pov.name not in [x.text() for x in self.ui.btnFilter.actions()]:
            self._add_pov_filter_action(self.editor.scene.pov)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageView)
        self.editor.widget.deleteLater()
        self.editor = None

        emit_event(SceneChangedEvent(self))
        self.refresh()

    def _on_new(self):
        self.editor = SceneEditor(self.novel)
        self._switch_to_editor()

    def _new_chapter(self):
        self.chaptersModel.newChapter()
        client.update_novel(self.novel)

    def _update_cards(self):
        self.scene_cards.clear()
        self.selected_card = None
        self._cards_layout.clear()

        for scene in self.novel.scenes:
            card = SceneCard(scene)
            self._cards_layout.addWidget(card)
            self.scene_cards.append(card)
            card.selected.connect(self._card_selected)
            card.doubleClicked.connect(self._on_edit)

    def _card_selected(self, card: SceneCard):
        if self.selected_card and self.selected_card is not card:
            self.selected_card.clearSelection()
        self.selected_card = card
        self.ui.btnDelete.setEnabled(True)
        self.ui.btnEdit.setEnabled(True)

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
        elif self.ui.btnTimelineView.isChecked():
            self.ui.stackScenes.setCurrentWidget(self.ui.pageTimeline)
            self.ui.tblScenes.clearSelection()
            self.ui.tblSceneStages.clearSelection()
            if not self.timeline_view:
                self.timeline_view = TimelineView(self.novel)
                self.ui.pageTimeline.layout().addWidget(self.timeline_view.widget)
        elif self.ui.btnCharactersDistributionView.isChecked():
            self.ui.stackScenes.setCurrentWidget(self.ui.pageCharactersDistribution)
            self.ui.tblScenes.clearSelection()
            self.ui.tblSceneStages.clearSelection()
            if not self.characters_distribution:
                self.characters_distribution = CharactersScenesDistributionWidget(self.novel)
                self.ui.pageCharactersDistribution.layout().addWidget(self.characters_distribution)
        else:
            self.ui.stackScenes.setCurrentWidget(self.ui.pageDefault)
            self.ui.tblSceneStages.clearSelection()

        if self.ui.btnActionsView.isChecked():
            columns = self._actions_view_columns
            height = 60
            relax_colors = True
            self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColBeginning,
                                                                      QHeaderView.Stretch)
            self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColMiddle,
                                                                      QHeaderView.Stretch)
        self.tblModel.setRelaxColors(relax_colors)
        for col in range(self.tblModel.columnCount()):
            if col in columns:
                self.ui.tblScenes.showColumn(col)
                continue
            self.ui.tblScenes.hideColumn(col)
        self.ui.tblScenes.verticalHeader().setDefaultSectionSize(height)

    def _init_stages_view(self):
        self.stagesModel = ScenesStageTableModel(self.novel)
        self.ui.tblSceneStages.setModel(self.stagesModel)
        self.ui.tblSceneStages.verticalHeader().setStyleSheet(
            '''QHeaderView::section {background-color: white; border: 0px; color: black; font-size: 14px;}
               QHeaderView {background-color: white;}''')
        self.ui.tblSceneStages.verticalHeader().setFixedWidth(40)
        self.ui.tblSceneStages.setColumnWidth(ScenesStageTableModel.ColTitle, 250)

        for col in range(1, self.stagesModel.columnCount()):
            self.ui.tblSceneStages.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
            w = self.ui.tblSceneStages.horizontalHeader().sectionSize(col)
            self.ui.tblSceneStages.horizontalHeader().setSectionResizeMode(col, QHeaderView.Interactive)
            self.ui.tblSceneStages.setColumnWidth(col, w + 10)
        self.stagesProgress = SceneStageProgressCharts(self.novel)

        self.ui.tblSceneStages.clicked.connect(self.stagesModel.changeStage)
        self.ui.tblSceneStages.clicked.connect(self.stagesProgress.refresh)

        if self.novel.scenes:
            self.stagesProgress.refresh()
            for i, chartview in enumerate(self.stagesProgress.charts()):
                self.ui.wdgProgressCharts.layout().insertWidget(i, chartview)

    def _on_custom_menu_requested(self, pos: QPoint):
        def toggle_wip(scene: Scene):
            scene.wip = not scene.wip
            client.update_scene(scene)
            self.refresh()

        index: QModelIndex = self.ui.tblScenes.indexAt(pos)
        scene: Scene = index.data(ScenesTableModel.SceneRole)

        menu = QMenu(self.ui.tblScenes)
        menu.addAction(IconRegistry.wip_icon(), 'Toggle WIP status', lambda: toggle_wip(scene))
        menu.addAction(IconRegistry.plus_icon(), 'Insert new scene', lambda: self._insert_scene_after(index))

        menu.popup(self.ui.tblScenes.viewport().mapToGlobal(pos))

    def _insert_scene_after(self, index: QModelIndex):
        new_scene = index.data(ScenesTableModel.SceneRole)
        i = self.novel.scenes.index(new_scene)
        day = new_scene.day

        new_scene = Scene('Untitled', day=day)
        self.novel.scenes.insert(i + 1, new_scene)
        new_scene.sequence = i + 1
        client.insert_scene(self.novel, new_scene)
        self.refresh()
        self.commands_sent.emit(self.widget, [EditorCommand(EditorCommandType.UPDATE_SCENE_SEQUENCES)])

    def _on_delete(self):
        indexes = self.ui.tblScenes.selectedIndexes()
        if indexes:
            scene = indexes[0].data(role=ScenesTableModel.SceneRole)
            if not ask_confirmation(f'Are you sure you want to delete scene {scene.title}?'):
                return
            self.novel.scenes.remove(scene)
            client.delete_scene(self.novel, scene)
            self.refresh()
            self.commands_sent.emit(self.widget, [EditorCommand(EditorCommandType.UPDATE_SCENE_SEQUENCES)])
            emit_event(SceneDeletedEvent(self))

    def _on_scene_moved(self):
        self.commands_sent.emit(self.widget, [EditorCommand(EditorCommandType.UPDATE_SCENE_SEQUENCES)])
        self.refresh()

# class ScenesViewDelegate(QStyledItemDelegate):
#     avatarSize: int = 24
#
#     @overrides
#     def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
#         super(ScenesViewDelegate, self).paint(painter, option, index)
#         if index.column() == ScenesTableModel.ColCharacters:
#             scene: Scene = index.data(ScenesTableModel.SceneRole)
#             x = 3
#             if scene.pov:
#                 self._drawAvatar(painter, option, x, scene.pov)
#             x += 27
#             for char in scene.characters:
#                 self._drawAvatar(painter, option, x, char)
#                 x += 27
#                 if x + 27 >= option.rect.width():
#                     return
#
#         elif index.column() == ScenesTableModel.ColArc:
#             scene = index.data(ScenesTableModel.SceneRole)
#             painter.drawPixmap(option.rect.x() + 3, option.rect.y() + 2,
#                                IconRegistry.emotion_icon_from_feeling(scene.pov_arc()).pixmap(
#                                    QSize(self.avatarSize, self.avatarSize)))
#
#     def _drawAvatar(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', x: int, character: Character):
#         if character.avatar:
#             painter.drawPixmap(option.rect.x() + x, option.rect.y() + 8,
#                                avatars.pixmap(character).scaled(self.avatarSize, self.avatarSize, Qt.KeepAspectRatio,
#                                                                 Qt.SmoothTransformation))
#         else:
#             painter.drawPixmap(option.rect.x() + x, option.rect.y() + 8,
#                                avatars.name_initial_icon(character).pixmap(QSize(self.avatarSize, self.avatarSize)))
#
#     @overrides
#     def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
#         if index.column() == ScenesTableModel.ColArc:
#             return QComboBox(parent)
#         if index.column() == ScenesTableModel.ColTime:
#             return QSpinBox(parent)
#         return QTextEdit(parent)
#
#     @overrides
#     def setEditorData(self, editor: QWidget, index: QModelIndex):
#         edit_data = index.data(Qt.EditRole)
#         if not edit_data:
#             edit_data = index.data(Qt.DisplayRole)
#         if isinstance(editor, QTextEdit) or isinstance(editor, QLineEdit):
#             editor.setText(str(edit_data))
#         elif isinstance(editor, QSpinBox):
#             editor.setValue(edit_data)
#         elif isinstance(editor, QComboBox):
#             arc = index.data(ScenesTableModel.SceneRole).pov_arc()
#             editor.addItem(IconRegistry.emotion_icon_from_feeling(VERY_UNHAPPY), '', VERY_UNHAPPY)
#             if arc == VERY_UNHAPPY:
#                 editor.setCurrentIndex(0)
#             editor.addItem(IconRegistry.emotion_icon_from_feeling(UNHAPPY), '', UNHAPPY)
#             if arc == UNHAPPY:
#                 editor.setCurrentIndex(1)
#             editor.addItem(IconRegistry.emotion_icon_from_feeling(NEUTRAL), '', NEUTRAL)
#             if arc == NEUTRAL:
#                 editor.setCurrentIndex(2)
#             editor.addItem(IconRegistry.emotion_icon_from_feeling(HAPPY), '', HAPPY)
#             if arc == HAPPY:
#                 editor.setCurrentIndex(3)
#             editor.addItem(IconRegistry.emotion_icon_from_feeling(VERY_HAPPY), '', VERY_HAPPY)
#             if arc == VERY_HAPPY:
#                 editor.setCurrentIndex(4)
#
#             editor.activated.connect(lambda: self._commit_and_close(editor))
#             editor.showPopup()
#
#     @overrides
#     def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
#         if isinstance(editor, QComboBox):
#             model.setData(index, editor.currentData(Qt.UserRole))
#         elif isinstance(editor, QSpinBox):
#             model.setData(index, editor.value())
#         else:
#             model.setData(index, editor.toPlainText())
#         scene = index.data(ScenesTableModel.SceneRole)
#         client.update_scene(scene)
#
#     def _commit_and_close(self, editor):
#         self.commitData.emit(editor)
#         self.closeEditor.emit(editor)
