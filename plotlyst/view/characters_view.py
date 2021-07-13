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

from PyQt5.QtCore import QItemSelection
from PyQt5.QtWidgets import QWidget

from plotlyst.core.client import client
from plotlyst.core.domain import Novel
from plotlyst.model.characters_model import CharactersTableModel
from plotlyst.model.common import proxy
from plotlyst.view.character_editor import CharacterEditor
from plotlyst.view.common import ask_confirmation
from plotlyst.view.generated.characters_view_ui import Ui_CharactersView
from plotlyst.view.icons import IconRegistry


class CharactersView:

    def __init__(self, novel: Novel):
        self.novel = novel
        self.widget = QWidget()
        self.ui = Ui_CharactersView()
        self.ui.setupUi(self.widget)
        self.editor: Optional[CharacterEditor] = None

        self.model = CharactersTableModel(novel)
        self._proxy = proxy(self.model)
        self.ui.listCharacters.setModel(self._proxy)

        self.ui.listCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.ui.listCharacters.doubleClicked.connect(self.ui.btnEdit.click)
        self.ui.btnEdit.setIcon(IconRegistry.edit_icon())
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.setIcon(IconRegistry.plus_icon(color='white'))
        self.ui.btnNew.clicked.connect(self._on_new)
        self.ui.btnDelete.setIcon(IconRegistry.trash_can_icon(color='white'))
        self.ui.btnDelete.clicked.connect(self._on_delete)

    def refresh(self):
        self.model.modelReset.emit()

    def _on_character_selected(self, selection: QItemSelection):
        selection = len(selection.indexes()) > 0
        self.ui.btnDelete.setEnabled(selection)
        self.ui.btnEdit.setEnabled(selection)

    def _on_edit(self):
        indexes = self.ui.listCharacters.selectedIndexes()
        if indexes:
            character = indexes[0].data(role=CharactersTableModel.CharacterRole)
            self.editor = CharacterEditor(self.novel, character)
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

        self.model.modelReset.emit()

    def _on_new(self):
        self.editor = CharacterEditor(self.novel)
        self._switch_to_editor()

    def _move_character_up(self):
        indexes = self.ui.listCharacters.selectedIndexes()
        if indexes:
            index: int = indexes[0].row()
            if index < 1:
                return
            character = indexes[0].data(role=CharactersTableModel.CharacterRole)
            self.novel.characters.remove(character)
            self.novel.characters.insert(index - 1, character)
            self.model.modelReset.emit()

    def _move_character_down(self):
        indexes = self.ui.listCharacters.selectedIndexes()
        if indexes:
            index: int = indexes[0].row()
            if index >= len(self.novel.characters) - 1:
                return
            character = indexes[0].data(role=CharactersTableModel.CharacterRole)
            self.novel.characters.remove(character)
            self.novel.characters.insert(index + 1, character)
            self.model.modelReset.emit()

    def _on_delete(self):
        indexes = self.ui.listCharacters.selectedIndexes()
        if indexes:
            character = indexes[0].data(role=CharactersTableModel.CharacterRole)
            if not ask_confirmation(f'Are you sure you want to delete character {character.name}?'):
                return
            self.novel.characters.remove(character)
            client.delete_character(character)
            self.refresh()
