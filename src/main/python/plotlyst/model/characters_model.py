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
from typing import List, Any, Optional

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from overrides import overrides

from src.main.python.plotlyst.core.domain import Character, Novel, Scene
from src.main.python.plotlyst.view.icons import avatars


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
    selection_changed = pyqtSignal()

    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.scene: Optional[Scene] = None

    def setScene(self, scene: Scene):
        self.scene = scene

    @overrides
    def columnCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return 1

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not self.scene:
            return QVariant()

        character: Character = self._data[index.row()]
        if character is self.scene.pov:
            if role == Qt.ToolTipRole:
                return 'POV character'
        elif character in self.scene.characters:
            if role == Qt.FontRole:
                font = QFont()
                font.setBold(True)
                return font
            elif role == Qt.CheckStateRole:
                return Qt.Checked
        elif role == Qt.CheckStateRole:
            return Qt.Unchecked

        return super(CharactersSceneAssociationTableModel, self).data(index, role)

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if not self.scene:
            return flags
        if self._data[index.row()] is self.scene.pov:
            return Qt.NoItemFlags
        return flags | Qt.ItemIsUserCheckable

    def toggleSelection(self, index: QModelIndex):
        character = self._data[index.row()]
        if character is self.scene.pov:
            return
        if character in self.scene.characters:
            self.scene.characters.remove(character)
        else:
            self.scene.characters.append(character)

        self.selection_changed.emit()
        self.modelReset.emit()

    def update(self):
        if self.scene.pov in self.scene.characters:
            self.scene.characters.remove(self.scene.pov)
        self.modelReset.emit()
