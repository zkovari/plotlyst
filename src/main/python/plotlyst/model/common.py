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
from typing import List, Any, Set

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QAbstractItemModel, QSortFilterProxyModel, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush
from overrides import overrides

from src.main.python.plotlyst.core.domain import SelectionItem
from src.main.python.plotlyst.view.icons import IconRegistry


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


class SelectionItemsModel(QAbstractTableModel):
    selection_changed = pyqtSignal()
    item_edited = pyqtSignal()
    ItemRole: int = Qt.UserRole + 1

    ColIcon: int = 0
    ColBgColor: int = 1
    ColName: int = 2

    def __init__(self, parent=None):
        super(SelectionItemsModel, self).__init__(parent)
        self._checkable: bool = False
        self._checkable_column: int = 0
        self._checked: Set[SelectionItem] = set()
        self._editable: bool = True

    def selections(self) -> Set[SelectionItem]:
        return self._checked

    def setCheckable(self, checkable: bool, column: int):
        self._checkable = checkable
        self._checkable_column = column
        self.modelReset.emit()

    def setEditable(self, editable: bool):
        self._editable = editable
        self.modelReset.emit()

    def checkItem(self, item: SelectionItem):
        if self._checkable:
            self._checked.add(item)
            self.selection_changed.emit()

    def uncheckItem(self, item: SelectionItem):
        if self._checkable and item in self._checked:
            self._checked.remove(item)
            self.selection_changed.emit()

    def uncheckAll(self):
        self._checked.clear()
        self.modelReset.emit()

    def add(self) -> int:
        index = self._newItem()
        item = self.item(index)
        if self._checkable:
            self._checked.add(item)
            self.selection_changed.emit()

        self.modelReset.emit()

        return index.row()

    @abstractmethod
    def _newItem(self) -> QModelIndex:
        pass

    def remove(self, index: QModelIndex):
        if self._checkable:
            self.uncheckItem(self.item(index))
        self.modelReset.emit()

    @overrides
    def columnCount(self, parent: QModelIndex = None) -> int:
        return 3

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        item = self.item(index)
        if role == self.ItemRole:
            return item
        if index.column() == self.ColIcon and role == Qt.DecorationRole:
            if item.icon:
                return IconRegistry.from_name(item.icon,
                                              item.icon_color)
            return IconRegistry.from_name('fa5s.icons', color='lightgrey')
        if index.column() == self.ColIcon and role == Qt.BackgroundRole:
            if item.icon and item.icon_color in ['FFFFFF', 'white']:
                return QBrush(QColor('lightGrey'))
        if index.column() == self.ColName and role == Qt.DisplayRole:
            return item.text
        if role == Qt.CheckStateRole and self._checkable and index.column() == self._checkable_column:
            return Qt.Checked if item in self._checked else Qt.Unchecked
        if role == Qt.FontRole and self._checkable and index.column() == self._checkable_column:
            if item in self._checked:
                font = QFont()
                font.setBold(True)
                return font
        if index.column() == self.ColBgColor:
            if role == Qt.BackgroundRole and item.color_hexa:
                return QBrush(QColor(item.color_hexa))

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if self._checkable and index.column() == self._checkable_column:
            flags = flags | Qt.ItemIsUserCheckable
        if self._editable and self.columnIsEditable(index.column()):
            flags = flags | Qt.ItemIsEditable

        return flags

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.DisplayRole) -> bool:
        item: SelectionItem = self.item(index)
        if role == Qt.EditRole:
            was_checked = item in self._checked
            if was_checked:
                self._checked.remove(item)
            item.text = value
            if was_checked:
                self._checked.add(item)
            self.item_edited.emit()
            return True
        if role == Qt.DecorationRole:
            item.icon = value[0]
            item.icon_color = value[1]
            self.item_edited.emit()
            return True
        if role == Qt.CheckStateRole:
            if value == Qt.Checked:
                self._checked.add(item)
            elif value == Qt.Unchecked:
                self._checked.remove(item)
            self.selection_changed.emit()
            return True
        if role == Qt.BackgroundRole:
            item.color_hexa = value
            self.item_edited.emit()
            return True
        return False

    @abstractmethod
    def item(self, index: QModelIndex) -> SelectionItem:
        pass

    def defaultEditableColumn(self) -> int:
        return self.ColName

    def columnIsEditable(self, column: int) -> bool:
        return column == self.ColName
