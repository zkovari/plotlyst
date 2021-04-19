from PyQt5.QtCore import pyqtSignal, QSortFilterProxyModel, QItemSelection, Qt, QObject
from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView

from novel_outliner.core.domain import Scene, Novel
from novel_outliner.model.scenes_model import ScenesTableModel
from novel_outliner.view.common import EditorCommand
from novel_outliner.view.generated.scenes_view_ui import Ui_ScenesView


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
        self.ui.tblScenes.verticalHeader().sectionMoved.connect(lambda: print('row moved'))
        self.ui.tblScenes.verticalHeader().setSectionsMovable(True)
        self.ui.tblScenes.verticalHeader().setDragEnabled(True)
        self.ui.tblScenes.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColTitle, 250)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColType, 40)
        self.ui.tblScenes.setColumnWidth(ScenesTableModel.ColSynopsis, 400)

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
