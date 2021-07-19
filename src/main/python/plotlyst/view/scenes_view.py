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
from typing import Optional

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, QItemSelection, Qt, QObject, QModelIndex, \
    QAbstractItemModel, QPoint, QSize
from PyQt5.QtWidgets import QWidget, QHeaderView, QToolButton, QWidgetAction, QStyledItemDelegate, \
    QStyleOptionViewItem, QTextEdit, QMenu, QAction, QComboBox, QLineEdit, QSpinBox
from overrides import overrides

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Scene, Novel, VERY_UNHAPPY, UNHAPPY, NEUTRAL, HAPPY, VERY_HAPPY
from src.main.python.plotlyst.model.chapters_model import ChaptersTreeModel
from src.main.python.plotlyst.model.characters_model import CharactersScenesDistributionTableModel
from src.main.python.plotlyst.model.common import proxy
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel, ScenesFilterProxyModel
from src.main.python.plotlyst.view.common import EditorCommand, ask_confirmation, EditorCommandType
from src.main.python.plotlyst.view.generated.scene_dstribution_widget_ui import Ui_CharactersScenesDistributionWidget
from src.main.python.plotlyst.view.generated.scenes_view_ui import Ui_ScenesView
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.scene_editor import SceneEditor


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
        self._actions_view_columns = [ScenesTableModel.ColPov, ScenesTableModel.ColTitle, ScenesTableModel.ColBeginning,
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
        self.ui.btnNewChapter.setIcon(IconRegistry.plus_icon())
        self.ui.btnNewChapter.clicked.connect(self._new_chapter)

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

        menu = QMenu(self.ui.btnGraphs)
        action = QWidgetAction(menu)
        self._distribution_widget = CharactersScenesDistributionWidget(self.novel)
        self._distribution_widget.setMinimumWidth(900)
        self._distribution_widget.setMinimumHeight(600)
        action.setDefaultWidget(self._distribution_widget)
        menu.addAction(action)
        self.ui.btnGraphs.setMenu(menu)

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

        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.clicked.connect(self._on_new)
        self.ui.btnDelete.setIcon(IconRegistry.trash_can_icon(color='white'))
        self.ui.btnDelete.clicked.connect(self._on_delete)

    def refresh(self):
        self.tblModel.modelReset.emit()
        self.chaptersModel.update()
        self.chaptersModel.modelReset.emit()
        self._distribution_widget.refresh()

    def _on_scene_selected(self, selection: QItemSelection):
        selection = len(self.ui.tblScenes.selectedIndexes()) > 0
        self.ui.btnDelete.setEnabled(selection)
        self.ui.btnEdit.setEnabled(selection)
        if selection:
            self.ui.treeChapters.clearSelection()

    def _on_chapter_selected(self, selection: QItemSelection):
        selection = len(self.ui.treeChapters.selectedIndexes()) > 0
        if selection:
            self.ui.tblScenes.clearSelection()

    def _hide_chapters_toggled(self, toggled: bool):
        self.ui.wgtChapters.setHidden(toggled)
        self.ui.btnChaptersToggle.setIcon(IconRegistry.eye_open_icon() if toggled else IconRegistry.eye_closed_icon())

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

        self.refresh()

    def _on_new(self):
        self.editor = SceneEditor(self.novel)
        self._switch_to_editor()

    def _new_chapter(self):
        chapter = self.chaptersModel.newChapter()
        client.insert_chapter(self.novel, chapter)

    def _switch_view(self):
        height = 50
        relax_colors = False
        columns = self._default_columns

        if self.ui.btnSynopsisView.isChecked():
            columns = [ScenesTableModel.ColSynopsis, ScenesTableModel.ColPov]

        elif self.ui.btnActionsView.isChecked():
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

    @overrides
    def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        super(ScenesViewDelegate, self).paint(painter, option, index)
        if index.column() == ScenesTableModel.ColCharacters:
            scene: Scene = index.data(ScenesTableModel.SceneRole)
            x = 3
            if scene.pov:
                painter.drawPixmap(option.rect.x() + x, option.rect.y() + 8,
                                   avatars.pixmap(scene.pov).scaled(24, 24, Qt.KeepAspectRatio,
                                                                    Qt.SmoothTransformation))
            x += 27
            for char in scene.characters:
                if not char.avatar:
                    continue
                painter.drawPixmap(option.rect.x() + x, option.rect.y() + 8,
                                   avatars.pixmap(char).scaled(24, 24, Qt.KeepAspectRatio,
                                                               Qt.SmoothTransformation))
                x += 27
                if x + 27 >= option.rect.width():
                    return

        elif index.column() == ScenesTableModel.ColArc:
            scene = index.data(ScenesTableModel.SceneRole)
            painter.drawPixmap(option.rect.x() + 3, option.rect.y() + 2,
                               IconRegistry.emotion_icon_from_feeling(scene.pov_arc()).pixmap(QSize(24, 24)))

    @overrides
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.column() == ScenesTableModel.ColArc:
            return QComboBox(parent)
        if index.column() == ScenesTableModel.ColTime:
            return QSpinBox(parent)
        return QTextEdit(parent)

    @overrides
    def setEditorData(self, editor: QWidget, index: QModelIndex):
        edit_data = index.data(Qt.EditRole)
        if not edit_data:
            edit_data = index.data(Qt.DisplayRole)
        if isinstance(editor, QTextEdit) or isinstance(editor, QLineEdit):
            editor.setText(str(edit_data))
        elif isinstance(editor, QSpinBox):
            editor.setValue(edit_data)
        elif isinstance(editor, QComboBox):
            arc = index.data(ScenesTableModel.SceneRole).pov_arc()
            editor.addItem(IconRegistry.emotion_icon_from_feeling(VERY_UNHAPPY), '', VERY_UNHAPPY)
            if arc == VERY_UNHAPPY:
                editor.setCurrentIndex(0)
            editor.addItem(IconRegistry.emotion_icon_from_feeling(UNHAPPY), '', UNHAPPY)
            if arc == UNHAPPY:
                editor.setCurrentIndex(1)
            editor.addItem(IconRegistry.emotion_icon_from_feeling(NEUTRAL), '', NEUTRAL)
            if arc == NEUTRAL:
                editor.setCurrentIndex(2)
            editor.addItem(IconRegistry.emotion_icon_from_feeling(HAPPY), '', HAPPY)
            if arc == HAPPY:
                editor.setCurrentIndex(3)
            editor.addItem(IconRegistry.emotion_icon_from_feeling(VERY_HAPPY), '', VERY_HAPPY)
            if arc == VERY_HAPPY:
                editor.setCurrentIndex(4)

            editor.activated.connect(lambda: self._commit_and_close(editor))
            editor.showPopup()

    @overrides
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentData(Qt.UserRole))
        elif isinstance(editor, QSpinBox):
            model.setData(index, editor.value())
        else:
            model.setData(index, editor.toPlainText())
        scene = index.data(ScenesTableModel.SceneRole)
        client.update_scene(scene)

    def _commit_and_close(self, editor):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)


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
        self.ui.tblSceneDistribution.horizontalHeader().setDefaultSectionSize(26)
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
        self.ui.tblSceneDistribution.horizontalHeader().setMaximumSectionSize(15)
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
