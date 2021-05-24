from functools import partial
from typing import Any

from PyQt5.QtCore import pyqtSignal, QItemSelection, Qt, QObject, QModelIndex, \
    QAbstractItemModel, QPoint, QAbstractTableModel
from PyQt5.QtGui import QIcon, QBrush, QColor
from PyQt5.QtWidgets import QWidget, QHeaderView, QToolButton, QWidgetAction, QStyledItemDelegate, \
    QStyleOptionViewItem, QTextEdit, QMenu, QAction
from overrides import overrides

from novel_outliner.core.client import client
from novel_outliner.core.domain import Scene, Novel
from novel_outliner.model.characters_model import CharactersScenesDistributionTableModel
from novel_outliner.model.common import proxy
from novel_outliner.model.scenes_model import ScenesTableModel, ScenesFilterProxyModel
from novel_outliner.view.common import EditorCommand, ask_confirmation, EditorCommandType
from novel_outliner.view.generated.draft_scenes_view_ui import Ui_DraftScenesView
from novel_outliner.view.generated.scene_characters_widget_ui import Ui_SceneCharactersWidget
from novel_outliner.view.generated.scene_dstribution_widget_ui import Ui_CharactersScenesDistributionWidget
from novel_outliner.view.generated.scenes_view_ui import Ui_ScenesView
from novel_outliner.view.icons import IconRegistry, avatars


class ScenesOutlineView(QObject):
    commands_sent = pyqtSignal(QWidget, list)
    scene_edited = pyqtSignal(Scene)
    scene_created = pyqtSignal()

    def __init__(self, novel: Novel):
        super().__init__()
        self.novel = novel
        self.widget = QWidget()
        self.ui = Ui_ScenesView()
        self.ui.setupUi(self.widget)

        self.model = ScenesTableModel(novel)
        self._proxy = ScenesFilterProxyModel()
        self._proxy.setSourceModel(self.model)
        self._proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.ui.tblScenes.setModel(self._proxy)
        self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColTitle, QHeaderView.Fixed)
        self.ui.tblScenes.horizontalHeader().setFixedHeight(30)
        self.ui.tblScenes.verticalHeader().setStyleSheet(
            'QHeaderView::section {background-color: white; border: 0px; color: black; font-size: 14px;} QHeaderView {background-color: white;}')
        self.ui.tblScenes.verticalHeader().sectionMoved.connect(self._on_scene_moved)
        self.ui.tblScenes.verticalHeader().setFixedWidth(40)
        self.model.orderChanged.connect(self._on_scene_moved)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColTitle, 250)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColType, 55)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColPov, 60)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColSynopsis, 400)
        self._display_characters()
        self.ui.tblScenes.setItemDelegate(ScenesViewDelegate(self.novel))
        self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColCharacters,
                                                                  QHeaderView.ResizeToContents)
        self.ui.tblScenes.hideColumn(ScenesTableModel.ColTime)

        self.ui.btnGraphs.setPopupMode(QToolButton.InstantPopup)
        self.ui.btnGraphs.setIcon(IconRegistry.graph_icon())
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
        self.model.modelReset.emit()
        self._display_characters()

    def _on_scene_selected(self, selection: QItemSelection):
        selection = len(selection.indexes()) > 0
        self.ui.btnDelete.setEnabled(selection)
        self.ui.btnEdit.setEnabled(selection)

    def _on_edit(self):
        indexes = self.ui.tblScenes.selectedIndexes()
        if indexes:
            scene = indexes[0].data(role=ScenesTableModel.SceneRole)
            self.scene_edited.emit(scene)

    def _on_new(self):
        self.scene_created.emit()

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
        if index.column() == ScenesTableModel.ColSynopsis:
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
        self._scenes_model = CharactersScenesDistributionTableModel(self.novel)
        self._scenes_proxy = proxy(self._scenes_model)
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
        for col in range(self._scenes_model.columnCount()):
            if col == 0:
                continue
            self.ui.tblCharacters.hideColumn(col)
        self.ui.spinAverage.setValue(self.average)
        self._scenes_model.modelReset.emit()

    def _on_character_selected(self):
        selected = self.ui.tblCharacters.selectionModel().selectedIndexes()
        self._scenes_model.highlightCharacters(
            [self._scenes_proxy.mapToSource(x) for x in selected])

        if selected and len(selected) > 1:
            self.ui.spinAverage.setPrefix(self.common_text)
            self.ui.spinAverage.setValue(self._scenes_model.commonScenes())
        else:
            self.ui.spinAverage.setPrefix(self.avg_text)
            self.ui.spinAverage.setValue(self.average)

        self.ui.tblSceneDistribution.clearSelection()

    def _on_scene_selected(self, selection: QItemSelection):
        indexes = selection.indexes()
        if not indexes:
            return
        self._scenes_model.highlightScene(self._scenes_proxy.mapToSource(indexes[0]))
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
