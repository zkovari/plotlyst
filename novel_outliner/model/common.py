from typing import List, Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
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
        if orientation == Qt.Horizontal:
            return self.headers[section]

        return section
