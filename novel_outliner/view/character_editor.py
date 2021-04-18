from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, QModelIndex, Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QStyledItemDelegate, QStyleOptionViewItem, QLineEdit, QSpinBox, \
    QComboBox
from overrides import overrides

from novel_outliner.core.domain import Novel, Character
from novel_outliner.model.characters_model import CharacterEditorTableModel
from novel_outliner.view.common import EditorCommand
from novel_outliner.view.generated.character_editor_ui import Ui_CharacterEditor


class CharacterEditor(QObject):
    commands_sent = pyqtSignal(QWidget, list)

    def __init__(self, novel: Novel, character: Optional[Character] = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_CharacterEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel

        if character:
            self.character = character
            self._new_character = False
        else:
            self.character = Character('')
            self._new_character = True

        self.model = CharacterEditorTableModel(self.character)
        self.editor_delegate = CharacterEditorDelegate()
        self.ui.tblGeneral.setModel(self.model)
        self.ui.tblGeneral.setItemDelegate(self.editor_delegate)

        self.btn_save = self.ui.buttonBox.button(QDialogButtonBox.Save)
        self.btn_save.clicked.connect(self._on_saved)
        self.btn_cancel = self.ui.buttonBox.button(QDialogButtonBox.Cancel)
        self.btn_cancel.clicked.connect(self._on_cancel)

    def _on_saved(self):
        if self._new_character:
            self.novel.characters.append(self.character)
        self.commands_sent.emit(self.widget, [EditorCommand.SAVE, EditorCommand.CLOSE_CURRENT_EDITOR,
                                              EditorCommand.DISPLAY_CHARACTERS])

    def _on_cancel(self):
        self.commands_sent.emit(self.widget, [EditorCommand.CLOSE_CURRENT_EDITOR])


class CharacterEditorDelegate(QStyledItemDelegate):

    @overrides
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.row() == CharacterEditorTableModel.RowName:
            self.editor = QLineEdit(parent)
        elif index.row() == CharacterEditorTableModel.RowAge:
            self.editor = QSpinBox(parent)
        elif index.row() == CharacterEditorTableModel.RowPersonality:
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
        if index.row() == CharacterEditorTableModel.RowName:
            self.editor.setText(str(edit_data))
        elif index.row() == CharacterEditorTableModel.RowAge:
            self.editor.setValue(edit_data)
        elif index.row() == CharacterEditorTableModel.RowPersonality:
            self.editor.setCurrentText(edit_data)
            self.editor.showPopup()
