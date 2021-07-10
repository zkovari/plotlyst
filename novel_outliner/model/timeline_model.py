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
from PyQt5.QtCore import QModelIndex, QSortFilterProxyModel
from overrides import overrides

from novel_outliner.model.scenes_model import ScenesTableModel


class TimelineScenesFilterProxyModel(QSortFilterProxyModel):

    @overrides
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        filtered = super().filterAcceptsRow(source_row, source_parent)

        if not filtered:
            return filtered

        if self.sourceModel().data(self.sourceModel().index(source_row, ScenesTableModel.ColTime),
                                   role=ScenesTableModel.SceneRole).day == 0:
            return False
        return filtered
