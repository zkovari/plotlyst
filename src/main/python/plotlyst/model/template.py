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
from typing import Any

from PyQt5.QtCore import QModelIndex, Qt
from overrides import overrides

from src.main.python.plotlyst.core.domain import TemplateField, SelectionItem
from src.main.python.plotlyst.model.common import EditableItemsModel
from src.main.python.plotlyst.view.icons import IconRegistry


class TemplateFieldSelectionModel(EditableItemsModel):
    ItemRole: int = Qt.UserRole + 1

    ColIcon: int = 0
    ColName: int = 1

    def __init__(self, field: TemplateField):
        super(TemplateFieldSelectionModel, self).__init__()
        self._field = field

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self._field.selections)

    @overrides
    def columnCount(self, parent: QModelIndex = None) -> int:
        return 2

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
        return False
