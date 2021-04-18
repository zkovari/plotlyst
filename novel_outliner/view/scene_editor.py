from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, QModelIndex, Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QStyledItemDelegate, QStyleOptionViewItem, QLineEdit, QComboBox
from overrides import overrides

from novel_outliner.core.domain import Novel, Scene
from novel_outliner.model.scenes_model import SceneEditorTableModel
from novel_outliner.view.common import EditorCommand
from novel_outliner.view.generated.scene_editor_ui import Ui_SceneEditor


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

        self.model = SceneEditorTableModel(self.scene)
        self.editor_delegate = SceneEditorDelegate()
        self.ui.tblSceneEditor.setModel(self.model)
        self.ui.tblSceneEditor.setItemDelegate(self.editor_delegate)

        self.btn_save = self.ui.buttonBox.button(QDialogButtonBox.Save)
        self.btn_save.clicked.connect(self._on_saved)
        self.btn_cancel = self.ui.buttonBox.button(QDialogButtonBox.Cancel)
        self.btn_cancel.clicked.connect(self._on_cancel)

    def _on_saved(self):
        if self._new_scene:
            self.novel.scenes.append(self.scene)
        self.commands_sent.emit(self.widget, [EditorCommand.SAVE, EditorCommand.CLOSE_CURRENT_EDITOR,
                                              EditorCommand.DISPLAY_SCENES])

    def _on_cancel(self):
        self.commands_sent.emit(self.widget, [EditorCommand.CLOSE_CURRENT_EDITOR])


class SceneEditorDelegate(QStyledItemDelegate):

    @overrides
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.row() == SceneEditorTableModel.RowTitle:
            self.editor = QLineEdit(parent)
        elif index.row() == SceneEditorTableModel.RowPov:
            combo_box = QComboBox(parent)
            combo_box.activated.connect(lambda: self.commitData.emit(self.editor))
            combo_box.addItem('Active')
            combo_box.setItemData(0, QBrush(Qt.green), role=Qt.BackgroundRole)
            combo_box.addItem('OFF')
            combo_box.setItemData(1, QBrush(Qt.red), role=Qt.BackgroundRole)
            self.editor = combo_box

        return self.editor

    @overrides
    def setEditorData(self, editor: QWidget, index: QModelIndex):
        edit_data = index.data(Qt.EditRole)
        if not edit_data:
            edit_data = index.data(Qt.DisplayRole)
        if index.row() == SceneEditorTableModel.RowTitle:
            self.editor.setText(str(edit_data))
        elif index.row() == SceneEditorTableModel.RowPov:
            self.editor.setCurrentText(edit_data)
            self.editor.showPopup()
