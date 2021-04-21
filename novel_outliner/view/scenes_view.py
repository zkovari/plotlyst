from PyQt5.QtCore import pyqtSignal, QSortFilterProxyModel, QItemSelection, Qt, QObject, QModelIndex, QAbstractItemModel
from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView, QToolButton, QWidgetAction, QStyledItemDelegate, \
    QStyleOptionViewItem, QTextEdit
from overrides import overrides

from novel_outliner.core.domain import Scene, Novel
from novel_outliner.core.persistence import emit_save
from novel_outliner.model.characters_model import CharactersScenesDistributionTableModel
from novel_outliner.model.common import proxy
from novel_outliner.model.scenes_model import ScenesTableModel
from novel_outliner.view.common import EditorCommand, ask_confirmation
from novel_outliner.view.generated.scene_dstribution_widget_ui import Ui_CharactersScenesDistributionWidget
from novel_outliner.view.generated.scenes_view_ui import Ui_ScenesView
from novel_outliner.view.icons import IconRegistry


class ScenesView(QObject):
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
        self._proxy = QSortFilterProxyModel()
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
        self.ui.tblScenes.verticalHeader().setSectionsMovable(True)
        self.ui.tblScenes.verticalHeader().setDragEnabled(True)
        self.ui.tblScenes.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColTitle, 250)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColType, 55)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColPov, 60)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColSynopsis, 400)

        self.ui.tblScenes.setItemDelegate(ScenesViewDelegate(self.novel))

        self.ui.btnGraphs.setPopupMode(QToolButton.InstantPopup)
        self.ui.btnGraphs.setIcon(IconRegistry.graph_icon())
        action = QWidgetAction(self.ui.btnGraphs)
        self._distribution_widget = CharactersScenesDistributionWidget(self.novel)
        self._distribution_widget.setMinimumWidth(900)
        self._distribution_widget.setMinimumHeight(600)
        action.setDefaultWidget(self._distribution_widget)
        self.ui.btnGraphs.addAction(action)

        self.ui.tblScenes.selectionModel().selectionChanged.connect(self._on_scene_selected)
        self.ui.tblScenes.doubleClicked.connect(self.ui.btnEdit.click)
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.clicked.connect(self._on_new)
        self.ui.btnDelete.clicked.connect(self._on_delete)

    def refresh(self):
        self.model.modelReset.emit()

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

    def _on_delete(self):
        indexes = self.ui.tblScenes.selectedIndexes()
        if indexes:
            scene = indexes[0].data(role=ScenesTableModel.SceneRole)
            if not ask_confirmation(f'Are you sure you want to delete scene {scene.title}?'):
                return
            self.novel.scenes.remove(scene)
            self.commands_sent.emit(self.widget, [EditorCommand.SAVE])
            self.refresh()

    def _on_scene_moved(self, logical: int, old_visual: int, new_visual: int):
        scene: Scene = self.model.index(logical, 0).data(ScenesTableModel.SceneRole)
        self.novel.scenes.remove(scene)
        self.novel.scenes.insert(new_visual, scene)

        self.model.modelReset.emit()
        self.commands_sent.emit(self.widget, [EditorCommand.SAVE])


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
        emit_save(self.novel)


class CharactersScenesDistributionWidget(QWidget):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.ui = Ui_CharactersScenesDistributionWidget()
        self.ui.setupUi(self)
        self.novel = novel
        self._proxy = proxy(CharactersScenesDistributionTableModel(self.novel))
        self._proxy.sort(0, Qt.DescendingOrder)
        self.ui.tblSceneDistribution.setModel(self._proxy)
        self.ui.tblSceneDistribution.setColumnWidth(0, 70)
