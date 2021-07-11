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
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.clicked.connect(self._on_new)
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
