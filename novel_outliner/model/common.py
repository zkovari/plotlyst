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
