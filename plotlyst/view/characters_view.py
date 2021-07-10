from PyQt5.QtCore import QItemSelection, QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget

from plotlyst.core.client import client
from plotlyst.core.domain import Novel, Character
from plotlyst.model.characters_model import CharactersTableModel
from plotlyst.model.common import proxy
from plotlyst.view.common import EditorCommand, ask_confirmation
from plotlyst.view.generated.characters_view_ui import Ui_CharactersView
from plotlyst.view.icons import IconRegistry


class CharactersView(QObject):
    commands_sent = pyqtSignal(QWidget, list)
    character_edited = pyqtSignal(Character)
    character_created = pyqtSignal()

    def __init__(self, novel: Novel):
        super().__init__()
        self.novel = novel
        self.widget = QWidget()
        self.ui = Ui_CharactersView()
        self.ui.setupUi(self.widget)

        self.model = CharactersTableModel(novel)
        self._proxy = proxy(self.model)
        self.ui.listCharacters.setModel(self._proxy)

        self.ui.btnUp.setIcon(IconRegistry.arrow_up_thick_icon())
        self.ui.btnDown.setIcon(IconRegistry.arrow_down_thick_icon())

        self.ui.listCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.clicked.connect(self._on_new)
        self.ui.btnDelete.clicked.connect(self._on_delete)
        self.ui.lineEdit.textChanged.connect(self._proxy.setFilterRegExp)
        self.ui.btnUp.clicked.connect(self._move_character_up)
        self.ui.btnDown.clicked.connect(self._move_character_down)

    def refresh(self):
        self.model.modelReset.emit()

    def _on_character_selected(self, selection: QItemSelection):
        selection = len(selection.indexes()) > 0
        self.ui.btnDelete.setEnabled(selection)
        self.ui.btnEdit.setEnabled(selection)
        self.ui.btnUp.setEnabled(selection)
        self.ui.btnDown.setEnabled(selection)

    def _on_edit(self):
        indexes = self.ui.listCharacters.selectedIndexes()
        if indexes:
            character = indexes[0].data(role=CharactersTableModel.CharacterRole)
            self.character_edited.emit(character)

    def _on_new(self):
        self.character_created.emit()

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
            self.commands_sent.emit(self.widget, [EditorCommand.SAVE])

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
            self.commands_sent.emit(self.widget, [EditorCommand.SAVE])

    def _on_delete(self):
        indexes = self.ui.listCharacters.selectedIndexes()
        if indexes:
            character = indexes[0].data(role=CharactersTableModel.CharacterRole)
            if not ask_confirmation(f'Are you sure you want to delete character {character.name}?'):
                return
            self.novel.characters.remove(character)
            client.delete_character(character)
            # self.commands_sent.emit(self.widget, [EditorCommand.SAVE])
            self.refresh()
