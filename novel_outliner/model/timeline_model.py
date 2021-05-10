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
