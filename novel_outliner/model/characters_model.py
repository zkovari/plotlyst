from typing import List, Any, Optional

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant
from PyQt5.QtGui import QFont, QIcon, QBrush, QColor
from overrides import overrides

from novel_outliner.core.domain import Character, Novel, Scene
from novel_outliner.view.icons import avatars


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
        elif role == Qt.DecorationRole:
            return QIcon(avatars.pixmap(self._data[index.row()]))


class CharactersSceneAssociationTableModel(CharactersTableModel):

    def __init__(self, novel: Novel, scene: Scene):
        super().__init__(novel)
        self.scene = scene

    @overrides
    def columnCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return 1

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.CheckStateRole and index.column() == 0:
            return Qt.Checked if self._data[index.row()] in self.scene.characters else Qt.Unchecked
        elif role == Qt.FontRole:
            if self._data[index.row()] in self.scene.characters:
                font = QFont()
                font.setBold(True)
                return font
        return super(CharactersSceneAssociationTableModel, self).data(index, role)

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if role == Qt.CheckStateRole:
            if value == Qt.Checked:
                self.scene.characters.append(self._data[index.row()])
            else:
                self.scene.characters.remove(self._data[index.row()])
            return True
        else:
            return super(CharactersTableModel, self).setData(index, value, role)

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        return flags | Qt.ItemIsUserCheckable


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


class CharactersScenesDistributionTableModel(QAbstractTableModel):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self._highlighted_scene: Optional[QModelIndex] = None
        self._highlighted_characters: List[QModelIndex] = []

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.characters)

    @overrides
    def columnCount(self, parent: QModelIndex = None) -> int:
        return len(self.novel.scenes) + 1

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return

        if index.column() == 0:
            if role == Qt.DecorationRole:
                return QIcon(avatars.pixmap(self.novel.characters[index.row()]))
            if role == Qt.ToolTipRole:
                return self.novel.characters[index.row()].name
            elif role == Qt.DisplayRole:
                return len([x for x in self.novel.scenes if
                            self.novel.characters[index.row()] in x.characters or self.novel.characters[
                                index.row()] == x.pov])
            if role == Qt.ForegroundRole:
                if self._highlighted_characters and index not in self._highlighted_characters:
                    return QBrush(QColor(Qt.gray))
        elif role == Qt.ToolTipRole:
            tooltip = f'{index.column()}. {self.novel.scenes[index.column() - 1].title}'
            if self.novel.scenes[index.column() - 1].pivotal:
                tooltip += f' ({self.novel.scenes[index.column() - 1].pivotal})'
            return tooltip
        elif role == Qt.BackgroundRole:
            if self._match(index):
                if self._highlighted_scene:
                    if self._highlighted_scene.column() != index.column():
                        return QBrush(QColor(Qt.gray))
                if self._highlighted_characters:
                    if not all([self._match_by_row_col(x.row(), index.column()) for x in self._highlighted_characters]):
                        return QBrush(QColor(Qt.gray))
                if self.novel.scenes[index.column() - 1].wip:
                    return QBrush(QColor('#f2f763'))
                if self.novel.scenes[index.column() - 1].pivotal:
                    return QBrush(QColor('#f07762'))
                return QBrush(QColor('darkblue'))
        return QVariant()

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)

        if self._highlighted_scene and index.column() == 0:
            if not self._match_by_row_col(index.row(), self._highlighted_scene.column()):
                return Qt.NoItemFlags

        return flags

    def highlightScene(self, index: QModelIndex):
        if self._match(index):
            self._highlighted_scene = index
        else:
            self._highlighted_scene = None

        self._highlighted_characters.clear()
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))

    def highlightCharacters(self, indexes: List[QModelIndex]):
        self._highlighted_characters = indexes
        self._highlighted_scene = None
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))

    def commonScenes(self) -> int:
        matches = 0
        for y in range(1, self.columnCount()):
            if all(self._match_by_row_col(x.row(), y) for x in self._highlighted_characters):
                matches += 1
        return matches

    def _match(self, index: QModelIndex):
        return self._match_by_row_col(index.row(), index.column())

    def _match_by_row_col(self, row: int, column: int):
        return self.novel.characters[row] in self.novel.scenes[column - 1].characters or \
               self.novel.characters[row] == self.novel.scenes[column - 1].pov
