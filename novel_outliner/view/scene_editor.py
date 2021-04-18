from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, QModelIndex, Qt, QAbstractItemModel, QSortFilterProxyModel
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QStyledItemDelegate, QStyleOptionViewItem, QLineEdit, QComboBox
from overrides import overrides

from novel_outliner.core.domain import Novel, Scene
from novel_outliner.model.characters_model import CharactersSceneAssociationTableModel
from novel_outliner.model.scenes_model import SceneEditorTableModel
from novel_outliner.view.common import EditorCommand
from novel_outliner.view.generated.scene_editor_ui import Ui_SceneEditor
from novel_outliner.view.icons import IconRegistry


class SceneEditor(QObject):
    commands_sent = pyqtSignal(QWidget, list)

    def __init__(self, novel: Novel, scene: Optional[Scene] = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_SceneEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel

        if scene:
            self.scene = scene
            self._new_scene = False
        else:
            self.scene = Scene('')
            self._new_scene = True

        self.ui.tabWidget.setTabIcon(self.ui.tabWidget.indexOf(self.ui.tabGeneral), IconRegistry.general_info_icon())
        self.ui.tabWidget.setTabIcon(self.ui.tabWidget.indexOf(self.ui.tabCharacters), IconRegistry.character_icon())
        self.ui.tabWidget.setTabIcon(self.ui.tabWidget.indexOf(self.ui.tabSynopsis), IconRegistry.synopsis_icon())

        self.model = SceneEditorTableModel(self.scene)
        self.editor_delegate = SceneEditorDelegate(self.novel)
        self.ui.tblSceneEditor.setModel(self.model)
        self.ui.tblSceneEditor.setItemDelegate(self.editor_delegate)
        self.ui.tblSceneEditor.setColumnWidth(1, 200)

        self.ui.textSynopsis.setText(self.scene.synopsis)

        self._characters_model = CharactersSceneAssociationTableModel(self.novel, self.scene)
        self._characters_proxy_model = QSortFilterProxyModel()
        self._characters_proxy_model.setSourceModel(self._characters_model)
        self.ui.tblCharacters.setModel(self._characters_proxy_model)

        self.btn_save = self.ui.buttonBox.button(QDialogButtonBox.Save)
        self.btn_save.clicked.connect(self._on_saved)
        self.btn_cancel = self.ui.buttonBox.button(QDialogButtonBox.Cancel)
        self.btn_cancel.clicked.connect(self._on_cancel)

    def _on_saved(self):
        self.scene.synopsis = self.ui.textSynopsis.toPlainText()
        if self._new_scene:
            self.novel.scenes.append(self.scene)
        self.commands_sent.emit(self.widget, [EditorCommand.SAVE, EditorCommand.CLOSE_CURRENT_EDITOR,
                                              EditorCommand.DISPLAY_SCENES])

    def _on_cancel(self):
        self.commands_sent.emit(self.widget, [EditorCommand.CLOSE_CURRENT_EDITOR])


class SceneEditorDelegate(QStyledItemDelegate):

    def __init__(self, novel: Novel):
        super().__init__()
        self.novel = novel

    @overrides
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.row() == SceneEditorTableModel.RowPov:
            combo_box = QComboBox(parent)
            combo_box.activated.connect(lambda: self.commitData.emit(editor))
            for char in self.novel.characters:
                combo_box.addItem(char.name, char)
            editor = combo_box
        else:
            editor = QLineEdit(parent)

        return editor

    @overrides
    def setEditorData(self, editor: QWidget, index: QModelIndex):
        edit_data = index.data(Qt.EditRole)
        if not edit_data:
            edit_data = index.data(Qt.DisplayRole)
        if index.row() == SceneEditorTableModel.RowPov:
            editor.setCurrentText(edit_data)
            editor.showPopup()
        else:
            editor.setText(str(edit_data))

    @overrides
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if index.row() == SceneEditorTableModel.RowPov:
            character = editor.currentData()
            model.setData(index, character)
        else:
            super().setModelData(editor, model, index)
