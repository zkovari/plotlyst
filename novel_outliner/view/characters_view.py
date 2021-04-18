from PyQt5.QtCore import QItemSelection, QObject, pyqtSignal, QSortFilterProxyModel, Qt
from PyQt5.QtWidgets import QWidget

from novel_outliner.core.domain import Novel, Character
from novel_outliner.model.characters_model import CharactersTableModel
from novel_outliner.view.common import EditorCommand
from novel_outliner.view.generated.characters_view_ui import Ui_CharactersView


class CharactersView(QObject):
    commands_sent = pyqtSignal(QWidget, list)
    character_edited = pyqtSignal(Character)

    def __init__(self, novel: Novel):
        super().__init__()
        self.novel = novel
        self.widget = QWidget()
        self.ui = Ui_CharactersView()
        self.ui.setupUi(self.widget)

        self.model = CharactersTableModel(novel)
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self.model)
        self._proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.ui.listCharacters.setModel(self._proxy)

        self.ui.listCharacters.selectionModel().selectionChanged.connect(self._on_character_selected)
        self.ui.btnEdit.clicked.connect(self._on_edit)
        self.ui.btnNew.clicked.connect(self._on_new)
        self.ui.btnDelete.clicked.connect(self._on_delete)
        self.ui.lineEdit.textChanged.connect(self._proxy.setFilterRegExp)

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
            self.character_edited.emit(character)

    def _on_new(self):
        self.character_edited.emit(None)

    def _on_delete(self):
        indexes = self.ui.listCharacters.selectedIndexes()
        if indexes:
            character = indexes[0].data(role=CharactersTableModel.CharacterRole)
            self.novel.characters.remove(character)
            self.commands_sent.emit(self.widget, [EditorCommand.SAVE])
            self.refresh()
