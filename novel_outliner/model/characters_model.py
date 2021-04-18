from typing import List, Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant
from overrides import overrides

from novel_outliner.core.domain import Character, Novel


class CharactersTableModel(QAbstractTableModel):
    CharacterRole = Qt.UserRole + 1

    ColName = 0
    ColAge = 1

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._data: List[Character] = novel.characters
        self._headers = []
        for _ in range(2):
            self._headers.append('')
        self._headers[self.ColName] = 'Name'
        self._headers[self.ColAge] = 'Age'

    @overrides
    def rowCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return len(self._data)

    @overrides
    def columnCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return len(self._headers)

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()

        if role == self.CharacterRole:
            return self._data[index.row()]
        elif role == Qt.DisplayRole:
            if index.column() == self.ColName:
                return self._data[index.row()].name


class CharacterEditorTableModel(QAbstractTableModel):
    RowName = 0
    RowAge = 1
    RowPersonality = 2

    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self._data: Character = character

    @overrides
    def rowCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return 3

    @overrides
    def columnCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return 2

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            if index.row() == self.RowName:
                if index.column() == 0:
                    return 'Name'
                else:
                    return self._data.name
            elif index.row() == self.RowAge:
                if index.column() == 0:
                    return 'Age'
                else:
                    return self._data.age
            elif index.row() == self.RowPersonality:
                if index.column() == 0:
                    return 'Personality'
                else:
                    return self._data.personality

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if index.row() == self.RowName:
            self._data.name = value
        elif index.row() == self.RowAge:
            self._data.age = int(value)
        elif index.row() == self.RowPersonality:
            self._data.personality = value
        else:
            return False

        return True

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.column() == 1:
            return flags | Qt.ItemIsEditable
        return flags
