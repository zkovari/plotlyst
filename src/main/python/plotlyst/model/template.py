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
from typing import Any, Set

from PyQt5.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont
from overrides import overrides

from src.main.python.plotlyst.core.domain import TemplateField, SelectionItem
from src.main.python.plotlyst.model.common import EditableItemsModel
from src.main.python.plotlyst.view.icons import IconRegistry


class TemplateFieldSelectionModel(EditableItemsModel):
    selection_changed = pyqtSignal()
    ItemRole: int = Qt.UserRole + 1

    ColIcon: int = 0
    ColName: int = 1

    def __init__(self, field: TemplateField):
        super(TemplateFieldSelectionModel, self).__init__()
        self._field = field
        self._checkable: bool = False
        self._checkable_column: int = 0
        self._checked: Set[SelectionItem] = set()

    def selections(self) -> Set[SelectionItem]:
        return self._checked

    def setCheckable(self, checkable: bool, column: int):
        self._checkable = checkable
        self._checkable_column = column
        self.modelReset.emit()

    def checkItem(self, item: SelectionItem):
        if self._checkable:
            self._checked.add(item)

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self._field.selections)

    @overrides
    def columnCount(self, parent: QModelIndex = None) -> int:
        return 2

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super(TemplateFieldSelectionModel, self).flags(index)
        if self._checkable and index.column() == self._checkable_column:
            return Qt.ItemIsUserCheckable | flags
        return flags

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        item = self._field.selections[index.row()]
        if role == self.ItemRole:
            return item
        if index.column() == self.ColIcon and role == Qt.DecorationRole:
            if item.icon:
                return IconRegistry.from_name(item.icon,
                                              item.icon_color)
            return IconRegistry.from_name('fa5s.icons', color='lightgrey')
        if index.column() == self.ColName and role == Qt.DisplayRole:
            return item.text
        if role == Qt.CheckStateRole and self._checkable and index.column() == self._checkable_column:
            return Qt.Checked if item in self._checked else Qt.Unchecked
        if role == Qt.FontRole and self._checkable and index.column() == self._checkable_column:
            if item in self._checked:
                font = QFont()
                font.setBold(True)
                return font

    @overrides
    def add(self):
        self._field.selections.append(SelectionItem('New'))
        super(TemplateFieldSelectionModel, self).add()

    @overrides
    def remove(self, index: QModelIndex):
        self._field.selections.pop(index.row())
        super(TemplateFieldSelectionModel, self).remove(index)

    @overrides
    def defaultEditableColumn(self) -> int:
        return self.ColName

    @overrides
    def columnIsEditable(self, column: int) -> bool:
        return column == self.ColName

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.DisplayRole) -> bool:
        if role == Qt.EditRole:
            self._field.selections[index.row()].text = value
            return True
        if role == Qt.DecorationRole:
            self._field.selections[index.row()].icon = value[0]
            self._field.selections[index.row()].icon_color = value[1]
            return True
        if role == Qt.CheckStateRole:
            if value == Qt.Checked:
                self._checked.add(self._field.selections[index.row()])
            elif value == Qt.Unchecked:
                self._checked.remove(self._field.selections[index.row()])
            self.selection_changed.emit()
            return True
        return False


class TraitsFieldItemsSelectionModel(TemplateFieldSelectionModel):
    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super(TemplateFieldSelectionModel, self).flags(index)
        if self._checkable and index.column() == self._checkable_column:
            return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        return flags

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.ForegroundRole:
            item = self._field.selections[index.row()]
            brush = QBrush()
            if item.meta.get('positive', True):
                brush.setColor(QColor('#519872'))
            else:
                brush.setColor(QColor('#db5461'))
            return brush
        return super(TraitsFieldItemsSelectionModel, self).data(index, role)
