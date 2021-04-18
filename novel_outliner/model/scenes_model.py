from typing import List, Any

from PyQt5.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel
from overrides import overrides

from novel_outliner.core.domain import Novel, Scene
from novel_outliner.model.common import AbstractHorizontalHeaderBasedTableModel


class ScenesTableModel(AbstractHorizontalHeaderBasedTableModel):
    SceneRole = Qt.UserRole + 1

    ColTitle = 0
    ColPov = 1

    def __init__(self, novel: Novel, parent=None):
        self._data: List[Scene] = novel.scenes
        _headers = [''] * 2
        # for _ in range(2):
        #     _headers.append('')
        _headers[self.ColTitle] = 'Title'
        _headers[self.ColPov] = 'POV'
        super().__init__(_headers, parent)

    @overrides
    def rowCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return len(self._data)

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()

        if role == self.SceneRole:
            return self._data[index.row()]
        elif role == Qt.DisplayRole:
            if index.column() == self.ColTitle:
                return self._data[index.row()].title
            elif index.column() == self.ColPov:
                return self._data[index.row()].pov.name if self._data[index.row()].pov else ''


class SceneEditorTableModel(QAbstractTableModel):
    RowTitle = 0
    RowPov = 1

    def __init__(self, scene: Scene, parent=None):
        super().__init__(parent)
        self._data: Scene = scene

    @overrides
    def rowCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return 2

    @overrides
    def columnCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return 2

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            if index.row() == self.RowTitle:
                if index.column() == 0:
                    return 'Title'
                else:
                    return self._data.title
            elif index.row() == self.RowPov:
                if index.column() == 0:
                    return 'POV'
                else:
                    return self._data.pov.name if self._data.pov else ''

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if index.row() == self.RowTitle:
            self._data.title = value
        elif index.row() == self.RowPov:
            self._data.pov = int(value)
        else:
            return False

        return True

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.column() == 1:
            return flags | Qt.ItemIsEditable
        return flags
