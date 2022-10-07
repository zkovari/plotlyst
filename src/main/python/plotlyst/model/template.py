"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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

from PyQt6.QtCore import QModelIndex, Qt, QSortFilterProxyModel
from PyQt6.QtGui import QBrush, QColor
from overrides import overrides

from src.main.python.plotlyst.core.template import TemplateField, SelectionItem
from src.main.python.plotlyst.model.common import SelectionItemsModel


class TemplateFieldSelectionModel(SelectionItemsModel):

    def __init__(self, field: TemplateField):
        self._field = field
        super(TemplateFieldSelectionModel, self).__init__()

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self._field.selections)

    @overrides
    def _newItem(self) -> QModelIndex:
        self._field.selections.append(SelectionItem(''))
        return self.index(self.rowCount() - 1, 0)

    @overrides
    def _insertItem(self, row: int) -> QModelIndex:
        self._field.selections.insert(row, SelectionItem(''))
        return self.insert(row, 0)

    @overrides
    def remove(self, index: QModelIndex):
        super(TemplateFieldSelectionModel, self).remove(index)
        self._field.selections.pop(index.row())

    @overrides
    def item(self, index: QModelIndex) -> SelectionItem:
        return self._field.selections[index.row()]


class TraitsFieldItemsSelectionModel(TemplateFieldSelectionModel):
    PositivityRole = Qt.ItemDataRole.UserRole + 2

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        item = self._field.selections[index.row()]
        if role == Qt.ItemDataRole.ForegroundRole:
            brush = QBrush()
            if item.meta.get('positive', True):
                brush.setColor(QColor('#519872'))
            else:
                brush.setColor(QColor('#db5461'))
            return brush
        if role == self.PositivityRole:
            return item.meta.get('positive', True)
        return super(TraitsFieldItemsSelectionModel, self).data(index, role)

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.DisplayRole) -> bool:
        super_set = super(TraitsFieldItemsSelectionModel, self).setData(index, value, role)
        self.layoutChanged.emit()
        return super_set

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return Qt.ItemIsEnabled


class TraitsProxyModel(QSortFilterProxyModel):
    def __init__(self, positive: bool = True):
        super().__init__()
        self.positive = positive

    @overrides
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        filtered = super().filterAcceptsRow(source_row, source_parent)
        if not filtered:
            return filtered

        pos: bool = self.sourceModel().data(self.sourceModel().index(source_row, 0),
                                            role=TraitsFieldItemsSelectionModel.PositivityRole)

        return pos == self.positive
