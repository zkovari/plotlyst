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
from typing import Any, Optional

from PyQt5.QtCore import pyqtSignal, QItemSelection, Qt, QObject, QModelIndex, \
    QAbstractItemModel, QPoint, QAbstractTableModel
from PyQt5.QtGui import QIcon, QBrush, QColor
from PyQt5.QtWidgets import QWidget, QHeaderView, QToolButton, QWidgetAction, QStyledItemDelegate, \
    QStyleOptionViewItem, QTextEdit, QMenu, QAction
from overrides import overrides

from plotlyst.core.client import client
from plotlyst.core.domain import Scene, Novel
from plotlyst.model.chapters_model import ChaptersTreeModel
from plotlyst.model.characters_model import CharactersScenesDistributionTableModel
from plotlyst.model.common import proxy
from plotlyst.model.scenes_model import ScenesTableModel, ScenesFilterProxyModel
from plotlyst.view.common import EditorCommand, ask_confirmation, EditorCommandType
from plotlyst.view.generated.draft_scenes_view_ui import Ui_DraftScenesView
from plotlyst.view.generated.scene_characters_widget_ui import Ui_SceneCharactersWidget
from plotlyst.view.generated.scene_dstribution_widget_ui import Ui_CharactersScenesDistributionWidget
from plotlyst.view.generated.scenes_view_ui import Ui_ScenesView
from plotlyst.view.icons import IconRegistry, avatars
from plotlyst.view.scene_editor import SceneEditor


class ScenesOutlineView(QObject):
    commands_sent = pyqtSignal(QWidget, list)

    def __init__(self, novel: Novel):
        super().__init__()
        self.novel = novel
        self.widget = QWidget()
        self.ui = Ui_ScenesView()
        self.ui.setupUi(self.widget)

        self.editor: Optional[SceneEditor] = None

        self.tblModel = ScenesTableModel(novel)
        self._default_columns = [ScenesTableModel.ColTitle, ScenesTableModel.ColPov, ScenesTableModel.ColType,
                                 ScenesTableModel.ColCharacters,
                                 ScenesTableModel.ColSynopsis]
        self._actions_view_columns = [ScenesTableModel.ColPov, ScenesTableModel.ColBeginning,
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
        self.ui.tblScenes.verticalHeader().sectionMoved.connect(self._on_scene_moved)
        self.ui.tblScenes.verticalHeader().setFixedWidth(40)
        self.tblModel.orderChanged.connect(self._on_scene_moved)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColTitle, 250)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColType, 55)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColPov, 60)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColSynopsis, 400)
        self._display_characters()
        self.ui.tblScenes.setItemDelegate(ScenesViewDelegate(self.novel))
        self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColCharacters,
                                                                  QHeaderView.ResizeToContents)
        self.ui.tblScenes.hideColumn(ScenesTableModel.ColTime)

        self.ui.splitterLeft.setSizes([70, 500])

        self.chaptersModel = ChaptersTreeModel(self.novel)
        self.ui.treeChapters.setModel(self.chaptersModel)
        self.ui.treeChapters.expandAll()
        self.chaptersModel.orderChanged.connect(self._on_scene_moved)
        self.chaptersModel.modelReset.connect(self.ui.treeChapters.expandAll)
        self.ui.treeChapters.setColumnWidth(1, 20)
        self.ui.treeChapters.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.btnChaptersToggle.toggled.connect(self._hide_chapters_toggled)
        self.ui.btnNewChapter.setIcon(IconRegistry.plus_icon())
        self.ui.btnNewChapter.clicked.connect(self._new_chapter)

        self.ui.btnGraphs.setPopupMode(QToolButton.InstantPopup)
        self.ui.btnGraphs.setIcon(IconRegistry.graph_icon())
        self.ui.btnAct1.setIcon(IconRegistry.act_one_icon())
        self.ui.btnAct2.setIcon(IconRegistry.act_two_icon())
        self.ui.btnAct3.setIcon(IconRegistry.act_three_icon())
        self.ui.btnAct1.toggled.connect(partial(self._proxy.setActsFilter, 1))
        self.ui.btnAct2.toggled.connect(partial(self._proxy.setActsFilter, 2))
        self.ui.btnAct3.toggled.connect(partial(self._proxy.setActsFilter, 3))

        self.ui.btnTableView.setIcon(IconRegistry.table_icon())
        self.ui.btnTableView.toggled.connect(self._switch_view)
        self.ui.btnSynopsisView.setIcon(IconRegistry.synopsis_icon())
        self.ui.btnSynopsisView.toggled.connect(self._switch_view)
        self.ui.btnActionsView.setIcon(IconRegistry.action_scene_icon())
        self.ui.btnActionsView.toggled.connect(self._switch_view)
        self.ui.btnTableView.setChecked(True)

        action = QWidgetAction(self.ui.btnGraphs)
        self._distribution_widget = CharactersScenesDistributionWidget(self.novel)
        self._distribution_widget.setMinimumWidth(900)
        self._distribution_widget.setMinimumHeight(600)
        action.setDefaultWidget(self._distribution_widget)
        self.ui.btnGraphs.addAction(action)

        self.ui.btnFilter.setPopupMode(QToolButton.InstantPopup)
        self.ui.btnFilter.setIcon(IconRegistry.filter_icon())
        for pov in set([x.pov for x in self.novel.scenes if x.pov]):
            action = QAction(pov.name, self.ui.btnFilter)
            action.setCheckable(True)
            action.setChecked(True)
            action.triggered.connect(partial(self._proxy.setCharacterFilter, pov))
            self.ui.btnFilter.addAction(action)

        self.ui.tblScenes.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tblScenes.customContextMenuRequested.connect(self._on_custom_menu_requested)

        self.ui.tblScenes.selectionModel().selectionChanged.connect(self._on_scene_selected)
        self.ui.tblScenes.doubleClicked.connect(self.ui.btnEdit.click)
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.clicked.connect(self._on_new)
        self.ui.btnDelete.clicked.connect(self._on_delete)

    def _display_characters(self):
        for row in range(self._proxy.rowCount()):
            self.ui.tblScenes.setIndexWidget(self._proxy.index(row, ScenesTableModel.ColCharacters),
                                             SceneCharactersWidget(
                                                 self._proxy.index(row, 0).data(ScenesTableModel.SceneRole)))

    def refresh(self):
        self.tblModel.modelReset.emit()
        self._display_characters()

    def _on_scene_selected(self, selection: QItemSelection):
        selection = len(selection.indexes()) > 0
        self.ui.btnDelete.setEnabled(selection)
        self.ui.btnEdit.setEnabled(selection)

    def _hide_chapters_toggled(self, toggled: bool):
        self.ui.wgtChapters.setHidden(toggled)
        self.ui.btnChaptersToggle.setText('Show chapters' if toggled else 'Hide chapters')

    def _on_edit(self):
        indexes = self.ui.tblScenes.selectedIndexes()
        if indexes:
            scene = indexes[0].data(role=ScenesTableModel.SceneRole)
            self.editor = SceneEditor(self.novel, scene)
            self._switch_to_editor()

    def _switch_to_editor(self):
        self.ui.pageEditor.layout().addWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEditor)

        self.editor.ui.btnClose.clicked.connect(self._on_close_editor)

    def _on_close_editor(self):
        self.ui.pageEditor.layout().removeWidget(self.editor.widget)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageView)
        self.editor.widget.deleteLater()
        self.editor = None

        self.tblModel.modelReset.emit()
        self.chaptersModel.update()
        self._distribution_widget.refresh()

    def _on_new(self):
        self.editor = SceneEditor(self.novel)
        self._switch_to_editor()

    def _new_chapter(self):
        chapter = self.chaptersModel.newChapter()
        client.insert_chapter(self.novel, chapter)

    def _switch_view(self):
        if self.ui.btnTableView.isChecked():
            for col in range(self.tblModel.columnCount()):
                if col in self._default_columns:
                    self.ui.tblScenes.showColumn(col)
                    continue
                self.ui.tblScenes.hideColumn(col)

        elif self.ui.btnSynopsisView.isChecked():
            for col in range(self.tblModel.columnCount()):
                if col == ScenesTableModel.ColSynopsis or col == ScenesTableModel.ColPov:
                    self.ui.tblScenes.showColumn(col)
                    continue
                self.ui.tblScenes.hideColumn(col)

        elif self.ui.btnActionsView.isChecked():
            for col in range(self.tblModel.columnCount()):
                if col in self._actions_view_columns:
                    self.ui.tblScenes.showColumn(col)
                    continue
                self.ui.tblScenes.hideColumn(col)
            self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColBeginning,
                                                                      QHeaderView.Stretch)
            self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColMiddle,
                                                                      QHeaderView.Stretch)

    def _on_custom_menu_requested(self, pos: QPoint):
        def toggle_wip(scene: Scene):
            scene.wip = not scene.wip
            client.update_scene(scene)
            self.refresh()

        index: QModelIndex = self.ui.tblScenes.indexAt(pos)
        scene: Scene = index.data(ScenesTableModel.SceneRole)

        menu = QMenu(self.ui.tblScenes)

        wip_action = QAction('Toggle WIP status', menu)
        wip_action.triggered.connect(lambda: toggle_wip(scene))
        insert_action = QAction('Insert new scene', menu)
        insert_action.triggered.connect(lambda: self._insert_scene_after(index))
        menu.addAction(wip_action)
        menu.addAction(insert_action)

        menu.popup(self.ui.tblScenes.viewport().mapToGlobal(pos))

    def _insert_scene_after(self, index: QModelIndex):
        scene = index.data(ScenesTableModel.SceneRole)
        i = self.novel.scenes.index(scene)
        scene = Scene('Untitled')
        self.novel.scenes.insert(i + 1, scene)
        scene.sequence = i + 1
        client.insert_scene(self.novel, scene)
        self.refresh()
        self.commands_sent.emit(self.widget, [EditorCommand(EditorCommandType.UPDATE_SCENE_SEQUENCES)])

    def _on_delete(self):
        indexes = self.ui.tblScenes.selectedIndexes()
        if indexes:
            scene = indexes[0].data(role=ScenesTableModel.SceneRole)
            if not ask_confirmation(f'Are you sure you want to delete scene {scene.title}?'):
                return
            self.novel.scenes.remove(scene)
            client.delete_scene(scene)
            self.refresh()
            self.commands_sent.emit(self.widget, [EditorCommand(EditorCommandType.UPDATE_SCENE_SEQUENCES)])

    def _on_scene_moved(self):
        self.commands_sent.emit(self.widget, [EditorCommand(EditorCommandType.UPDATE_SCENE_SEQUENCES)])
        self.refresh()


class ScenesViewDelegate(QStyledItemDelegate):

    def __init__(self, novel: Novel):
        super().__init__()
        self.novel = novel

    @overrides
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        return QTextEdit(parent)

    @overrides
    def setEditorData(self, editor: QWidget, index: QModelIndex):
        edit_data = index.data(Qt.EditRole)
        if not edit_data:
            edit_data = index.data(Qt.DisplayRole)
        editor.setText(str(edit_data))

    @overrides
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        model.setData(index, editor.toPlainText())
        scene = index.data(ScenesTableModel.SceneRole)
        client.update_scene(scene)


class CharactersScenesDistributionWidget(QWidget):
    avg_text: str = 'Average characters per scenes: '
    common_text: str = 'Common scenes: '

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.ui = Ui_CharactersScenesDistributionWidget()
        self.ui.setupUi(self)
        self.novel = novel
        self.average = 0
        self._model = CharactersScenesDistributionTableModel(self.novel)
        self._scenes_proxy = proxy(self._model)
        self._scenes_proxy.sort(0, Qt.DescendingOrder)
        self.ui.tblSceneDistribution.setModel(self._scenes_proxy)
        self.ui.tblSceneDistribution.hideColumn(0)
        self.ui.tblCharacters.setModel(self._scenes_proxy)
        self.ui.tblCharacters.setColumnWidth(0, 70)
        self.ui.tblCharacters.setMaximumWidth(70)

        self.ui.tblCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.ui.tblSceneDistribution.selectionModel().selectionChanged.connect(self._on_scene_selected)

        self.refresh()

    def refresh(self):
        if self.novel.scenes:
            self.average = sum([len(x.characters) + 1 for x in self.novel.scenes]) / len(self.novel.scenes)
        else:
            self.average = 0
        for col in range(self._model.columnCount()):
            if col == 0:
                continue
            self.ui.tblCharacters.hideColumn(col)
        self.ui.spinAverage.setValue(self.average)
        self._model.modelReset.emit()

    def _on_character_selected(self):
        selected = self.ui.tblCharacters.selectionModel().selectedIndexes()
        self._model.highlightCharacters(
            [self._scenes_proxy.mapToSource(x) for x in selected])

        if selected and len(selected) > 1:
            self.ui.spinAverage.setPrefix(self.common_text)
            self.ui.spinAverage.setValue(self._model.commonScenes())
        else:
            self.ui.spinAverage.setPrefix(self.avg_text)
            self.ui.spinAverage.setValue(self.average)

        self.ui.tblSceneDistribution.clearSelection()

    def _on_scene_selected(self, selection: QItemSelection):
        indexes = selection.indexes()
        if not indexes:
            return
        self._model.highlightScene(self._scenes_proxy.mapToSource(indexes[0]))
        self.ui.tblCharacters.clearSelection()


class DraftScenesView:

    def __init__(self, novel: Novel):
        self.widget = QWidget()
        self.ui = Ui_DraftScenesView()
        self.ui.setupUi(self.widget)
        self.novel = novel

        self._model = ScenesTableModel(self.novel)
        self._proxy = proxy(self._model)
        self.ui.tblDraftScenes.setModel(self._proxy)


class SceneCharactersWidget(QWidget, Ui_SceneCharactersWidget):

    def __init__(self, scene: Scene, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.scene = scene

        self.model = self.Model(scene)
        self.tableView.setModel(self.model)
        if self.scene.wip:
            self.setStyleSheet('background: #f2f763')
        elif self.scene.pivotal:
            self.setStyleSheet('background: #f07762')

    class Model(QAbstractTableModel):
        def __init__(self, scene: Scene, parent=None):
            super().__init__(parent)
            self.scene = scene

        @overrides
        def rowCount(self, parent: QModelIndex = ...) -> int:
            return 1

        @overrides
        def columnCount(self, parent: QModelIndex = ...) -> int:
            return len(self.scene.characters) + 1

        @overrides
        def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
            if not index.isValid():
                return

            if role == Qt.DecorationRole:
                if index.column() == 0:
                    if self.scene.pov:
                        return QIcon(avatars.pixmap(self.scene.pov))
                else:
                    return QIcon(avatars.pixmap(self.scene.characters[index.column() - 1]))
            if role == Qt.BackgroundRole:
                if self.scene.wip:
                    return QBrush(QColor('#f2f763'))
                elif self.scene.pivotal:
                    return QBrush(QColor('#f07762'))
