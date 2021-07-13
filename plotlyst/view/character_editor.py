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
from typing import Optional

from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QWidget, QStyledItemDelegate, QStyleOptionViewItem, QLineEdit
from overrides import overrides

from plotlyst.core.client import client
from plotlyst.core.domain import Novel, Character
from plotlyst.model.characters_model import CharacterEditorTableModel
from plotlyst.view.generated.character_editor_ui import Ui_CharacterEditor


class CharacterEditor:

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
        self.model.valueChanged.connect(self._save)
        self.editor_delegate = CharacterEditorDelegate()
        self.ui.tblGeneral.setModel(self.model)
        self.ui.tblGeneral.setItemDelegate(self.editor_delegate)

    def _save(self):
        if self._new_character:
            self.novel.characters.append(self.character)
            client.insert_character(self.novel, self.character)
        else:
            client.update_character(self.character)
        self._new_character = False


class CharacterEditorDelegate(QStyledItemDelegate):

    @overrides
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        return QLineEdit(parent)

    @overrides
    def setEditorData(self, editor: QWidget, index: QModelIndex):
        edit_data = index.data(Qt.EditRole)
        if not edit_data:
            edit_data = index.data(Qt.DisplayRole)
        if index.row() == CharacterEditorTableModel.RowName:
            editor.setText(str(edit_data))
