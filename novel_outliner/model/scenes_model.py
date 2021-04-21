from typing import List, Any

from PyQt5.QtCore import QModelIndex, Qt, QVariant
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
                    return IconRegistry.action_scene_icon()
                elif self._data[index.row()].type == REACTION_SCENE:
                    return IconRegistry.reaction_scene_icon()
                else:
                    return IconRegistry.custom_scene_icon()
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
        elif role == Qt.DisplayRole:
            return str(section + 1)
        if role == Qt.DecorationRole:
            return IconRegistry.hashtag_icon()

    @overrides
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if index.column() == self.ColSynopsis:
            self._data[index.row()].synopsis = value
            return True

        return False

    @overrides
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.column() == self.ColSynopsis:
            return flags | Qt.ItemIsEditable
        return flags
