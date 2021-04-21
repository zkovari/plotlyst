from PyQt5.QtCore import pyqtSignal, QSortFilterProxyModel, QItemSelection, Qt, QObject
from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView, QToolButton, QWidgetAction

from novel_outliner.core.domain import Scene, Novel
from novel_outliner.model.characters_model import CharactersScenesDistributionTableModel
from novel_outliner.model.scenes_model import ScenesTableModel
from novel_outliner.view.common import EditorCommand
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
            'QHeaderView::section {background-color: white; border: 0px;} QHeaderView {background-color: white;}')
        self.ui.tblScenes.verticalHeader().sectionMoved.connect(self._on_scene_moved)
        self.ui.tblScenes.verticalHeader().setSectionsMovable(True)
        self.ui.tblScenes.verticalHeader().setDragEnabled(True)
        self.ui.tblScenes.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColTitle, 250)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColType, 55)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColPov, 60)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColSynopsis, 400)

        self.ui.btnGraphs.setPopupMode(QToolButton.InstantPopup)
        self.ui.btnGraphs.setIcon(IconRegistry.graph_icon())
        action = QWidgetAction(self.ui.btnGraphs)
        self._distribution_widget = CharactersScenesDistributionWidget(self.novel)
        self._distribution_widget.setMinimumWidth(500)
        self._distribution_widget.setMinimumHeight(600)
        action.setDefaultWidget(self._distribution_widget)
        self.ui.btnGraphs.addAction(action)

        self.ui.tblScenes.selectionModel().selectionChanged.connect(self._on_scene_selected)
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
            self.novel.scenes.remove(scene)
            self.commands_sent.emit(self.widget, [EditorCommand.SAVE])
            self.refresh()

    def _on_scene_moved(self, logical: int, old_visual: int, new_visual: int):
        scene: Scene = self.model.index(logical, 0).data(ScenesTableModel.SceneRole)
        self.novel.scenes.remove(scene)
        self.novel.scenes.insert(new_visual, scene)

        self.model.modelReset.emit()
        self.commands_sent.emit(self.widget, [EditorCommand.SAVE])


class CharactersScenesDistributionWidget(QWidget):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.ui = Ui_CharactersScenesDistributionWidget()
        self.ui.setupUi(self)
        self.novel = novel
        self.ui.tblSceneDistribution.setModel(CharactersScenesDistributionTableModel(self.novel))
