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
from abc import abstractmethod
from typing import List, Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QAbstractItemModel, QSortFilterProxyModel
from overrides import overrides


class AbstractHorizontalHeaderBasedTableModel(QAbstractTableModel):

    def __init__(self, headers: List[str], parent=None):
        super().__init__(parent)
        self.headers = headers

    @overrides
    def columnCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return len(self.headers)

    @overrides
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.headers[section]

            return str(section + 1)
        return super().headerData(section, orientation, role)


def proxy(model: QAbstractItemModel) -> QSortFilterProxyModel:
    _proxy = QSortFilterProxyModel()
    _proxy.setSourceModel(model)
    _proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
    _proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

    return _proxy


class EditableItemsModel(QAbstractTableModel):

    def add(self):
        self.modelReset.emit()

    def remove(self, index: QModelIndex):
        self.modelReset.emit()

    def defaultEditableColumn(self) -> int:
        return -1

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if self.columnIsEditable(index.column()):
            return flags | Qt.ItemIsEditable
        else:
            return flags

    @abstractmethod
    def columnIsEditable(self, column: int) -> bool:
        pass
