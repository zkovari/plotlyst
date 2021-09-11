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
from typing import List, Any

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

    def __init__(self, novel: Novel, scene: Scene):
        super().__init__(novel)
        self.scene = scene

    @overrides
    def columnCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return 1

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.CheckStateRole:
            if self._data[index.row()] is self.scene.pov:
                return Qt.Checked
            return Qt.Checked if self._data[index.row()] in self.scene.characters else Qt.Unchecked
        elif role == Qt.FontRole:
            if self._data[index.row()] in self.scene.characters:
                font = QFont()
                font.setBold(True)
                return font
        elif role == Qt.ToolTipRole:
            if self._data[index.row()] is self.scene.pov:
                return 'POV character'
        return super(CharactersSceneAssociationTableModel, self).data(index, role)

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if role == Qt.CheckStateRole:
            if value == Qt.Checked:
                self.scene.characters.append(self._data[index.row()])
            else:
                self.scene.characters.remove(self._data[index.row()])
            self.selection_changed.emit()
            return True
        else:
            return super(CharactersTableModel, self).setData(index, value, role)

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if self._data[index.row()] is self.scene.pov:
            return Qt.NoItemFlags
        return flags | Qt.ItemIsUserCheckable

    def update(self):
        if self.scene.pov in self.scene.characters:
            self.scene.characters.remove(self.scene.pov)
        self.modelReset.emit()
