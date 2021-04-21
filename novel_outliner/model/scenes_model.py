from typing import List, Any

from PyQt5.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel
from PyQt5.QtGui import QIcon
from overrides import overrides

from novel_outliner.core.domain import Novel, Scene, ACTION_SCENE, REACTION_SCENE
from novel_outliner.model.common import AbstractHorizontalHeaderBasedTableModel
from novel_outliner.view.icons import IconRegistry, avatars


class ScenesTableModel(AbstractHorizontalHeaderBasedTableModel):
    SceneRole = Qt.UserRole + 1

    ColPov = 0
    ColTitle = 1
    ColCharacters = 2
    ColType = 3
    ColSynopsis = 4

    def __init__(self, novel: Novel, parent=None):
        self._data: List[Scene] = novel.scenes
        _headers = [''] * 5
        _headers[self.ColTitle] = 'Title'
        _headers[self.ColType] = 'Type'
        _headers[self.ColPov] = 'POV'
        _headers[self.ColCharacters] = 'Characters'
        _headers[self.ColSynopsis] = 'Synopsis'
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
            elif index.column() == self.ColCharacters:
                return ', '.join([x.name for x in self._data[index.row()].characters])
            elif index.column() == self.ColSynopsis:
                return self._data[index.row()].synopsis
        elif role == Qt.DecorationRole:
            if index.column() == self.ColType:
                if self._data[index.row()].type == ACTION_SCENE:
                    return IconRegistry.action_scene()
                elif self._data[index.row()].type == REACTION_SCENE:
                    return IconRegistry.reaction_scene()
            elif index.column() == self.ColPov:
                if self._data[index.row()].pov:
                    return QIcon(avatars.pixmap(self._data[index.row()].pov))
        elif role == Qt.ToolTipRole:
            if index.column() == self.ColType:
                if self._data[index.row()].event_1:
                    tip = f' - {self._data[index.row()].event_1}\n\n'
                    tip += f' - {self._data[index.row()].event_2}\n\n'
                    tip += f' - {self._data[index.row()].event_3}'
                    return tip
            elif index.column() == self.ColPov:
                return self._data[index.row()].pov.name if self._data[index.row()].pov else ''
            elif index.column() == self.ColSynopsis:
                return self._data[index.row()].synopsis

    @overrides
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal:
            return super(ScenesTableModel, self).headerData(section, orientation, role)
        if role == Qt.DecorationRole:
            return IconRegistry.hashtag_icon()
        # return super(ScenesTableModel, self).headerData(section, orientation, role)


class SceneEditorTableModel(QAbstractTableModel):
    RowTitle = 0
    RowPov = 1
    RowType = 2

    def __init__(self, scene: Scene, parent=None):
        super().__init__(parent)
        self._data: Scene = scene

    @overrides
    def rowCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return 3

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
            elif index.row() == self.RowType:
                if index.column() == 0:
                    return 'Type'
                else:
                    return self._data.type
        elif role == Qt.DecorationRole:
            if index.row() == self.RowType and index.column() == 1:
                if self._data.type == ACTION_SCENE:
                    return IconRegistry.action_scene()
                elif self._data.type == REACTION_SCENE:
                    return IconRegistry.reaction_scene()

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if index.row() == self.RowTitle:
            self._data.title = value
        elif index.row() == self.RowPov:
            self._data.pov = value
        elif index.row() == self.RowType:
            self._data.type = value
        else:
            return False

        return True

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.column() == 1:
            return flags | Qt.ItemIsEditable
        return flags
