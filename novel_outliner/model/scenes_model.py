import pickle
from typing import List, Any, Dict, Optional

from PyQt5.QtCore import QModelIndex, Qt, QVariant, QSortFilterProxyModel, QMimeData, QByteArray, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QBrush, QColor
from overrides import overrides

from novel_outliner.core.domain import Novel, Scene, ACTION_SCENE, REACTION_SCENE, Character
from novel_outliner.model.common import AbstractHorizontalHeaderBasedTableModel
from novel_outliner.view.icons import IconRegistry, avatars


class ScenesTableModel(AbstractHorizontalHeaderBasedTableModel):
    orderChanged = pyqtSignal()
    SceneRole = Qt.UserRole + 1

    MimeType: str = 'application/scene'

    ColPov = 0
    ColTitle = 1
    ColCharacters = 2
    ColType = 3
    ColTime = 4
    ColSynopsis = 5

    def __init__(self, novel: Novel, parent=None):
        self._data: List[Scene] = novel.scenes
        _headers = [''] * 6
        _headers[self.ColTitle] = 'Title'
        _headers[self.ColType] = 'Type'
        _headers[self.ColPov] = 'POV'
        _headers[self.ColCharacters] = 'Characters'
        _headers[self.ColTime] = 'Day'
        _headers[self.ColSynopsis] = 'Synopsis'
        super().__init__(_headers, parent)
        self._second_act_start: Optional[QModelIndex] = None
        self._third_act_start: Optional[QModelIndex] = None

        self._find_acts()

    @overrides
    def rowCount(self, parent: QModelIndex = Qt.DisplayRole) -> int:
        return len(self._data)

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()

        if role == self.SceneRole:
            return self._data[index.row()]
        elif role == Qt.FontRole:
            if self._data[index.row()].wip:
                font = QFont()
                font.setItalic(True)
                return font
        elif role == Qt.BackgroundRole:
            if self._data[index.row()].wip:
                return QBrush(QColor('#f2f763'))
            elif self._data[index.row()].pivotal:
                return QBrush(QColor('#f07762'))
        elif role == Qt.DisplayRole:
            if index.column() == self.ColTitle:
                return self._data[index.row()].title
            elif index.column() == self.ColSynopsis:
                return self._data[index.row()].synopsis
            elif index.column() == self.ColTime:
                return self._data[index.row()].day
        elif role == Qt.DecorationRole:
            if index.column() == self.ColType:
                if self._data[index.row()].wip:
                    return IconRegistry.wip_icon()
                elif self._data[index.row()].type == ACTION_SCENE:
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
                if self._data[index.row()].beginning:
                    tip = f' - {self._data[index.row()].beginning}\n\n'
                    tip += f' - {self._data[index.row()].middle}\n\n'
                    tip += f' - {self._data[index.row()].end}'
                    return tip
                elif self._data[index.row()].middle:
                    return self._data[index.row()].middle
                elif self._data[index.row()].end:
                    return self._data[index.row()].end
            elif index.column() == self.ColPov:
                return self._data[index.row()].pov.name if self._data[index.row()].pov else ''
            elif index.column() == self.ColSynopsis:
                return self._data[index.row()].synopsis

    @overrides
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal:
            return super(ScenesTableModel, self).headerData(section, orientation, role)
        else:
            if role == Qt.DisplayRole:
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
        flags = flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        if index.column() == self.ColSynopsis:
            return flags | Qt.ItemIsEditable
        return flags

    @overrides
    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        mime_data = QMimeData()
        scene = self._data[indexes[0].row()]
        mime_data.setData(self.MimeType, QByteArray(pickle.dumps(scene)))
        return mime_data

    @overrides
    def mimeTypes(self) -> List[str]:
        return [self.MimeType]

    @overrides
    def canDropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int,
                        parent: QModelIndex) -> bool:
        if row < 0:
            return False
        if not data.hasFormat(self.MimeType):
            return False

        return True

    @overrides
    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if row < 0:
            return False
        if not data.hasFormat(self.MimeType):
            return False

        scene: Scene = pickle.loads(data.data(self.MimeType))
        old_index = self._data.index(scene)
        if row < old_index:
            new_index = row
        else:
            new_index = row - 1
        self._data.insert(new_index, self._data.pop(old_index))

        self.orderChanged.emit()
        return True

    @overrides
    def beginResetModel(self) -> None:
        self._find_acts()
        super().beginResetModel()

    def isInAct(self, act: int, row: int) -> bool:
        if act == 1 and self._second_act_start:
            return row <= self._second_act_start.row()
        elif act == 2 and self._second_act_start and self._third_act_start:
            return self._second_act_start.row() < row <= self._third_act_start.row()
        elif act == 3 and self._third_act_start:
            return row > self._third_act_start.row()

        return False

    def _find_acts(self):
        for index, scene in enumerate(self._data):
            if scene.pivotal == 'First plot point':
                self._second_act_start = self.index(index, 0)
            elif scene.pivotal == 'Dark moment':
                self._third_act_start = self.index(index, 0)


class ScenesFilterProxyModel(QSortFilterProxyModel):

    def __init__(self):
        super().__init__()
        self.character_filter: Dict[Character, bool] = {}
        self.acts_filter: Dict[int, bool] = {}

    def setCharacterFilter(self, character: Character, filter: bool):
        self.character_filter[character] = filter
        self.invalidateFilter()

    def setActsFilter(self, act: int, filter: bool):
        self.acts_filter[act] = filter
        self.invalidateFilter()

    @overrides
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        filtered = super(ScenesFilterProxyModel, self).filterAcceptsRow(source_row, source_parent)

        if not filtered:
            return filtered

        scene: Scene = self.sourceModel().data(self.sourceModel().index(source_row, 0), role=ScenesTableModel.SceneRole)
        if not scene:
            return filtered
        if not self.character_filter.get(scene.pov, True):
            return False

        for act, toggled in self.acts_filter.items():
            if self.sourceModel().isInAct(act, source_row) and not toggled:
                return False

        return filtered
