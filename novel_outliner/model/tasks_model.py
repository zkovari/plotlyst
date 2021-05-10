from typing import Any, List

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from overrides import overrides

from novel_outliner.core.domain import Task, Scene, Character
from novel_outliner.view.icons import IconRegistry


class TasksTableModel(QAbstractTableModel):
    ColType = 0
    ColRef = 1
    ColMessage = 2

    def __init__(self, tasks: List[Task], parent=None):
        super().__init__(parent)
        self.tasks = tasks

    @overrides
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.tasks)

    @overrides
    def columnCount(self, parent: QModelIndex = None) -> int:
        return 3

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return

        if index.column() == self.ColRef:
            if self.tasks[index.row()].reference:
                if isinstance(self.tasks[index.row()].reference, Scene):
                    if role == Qt.DisplayRole:
                        return self.tasks[index.row()].reference.title
                    if role == Qt.DecorationRole:
                        return IconRegistry.scene_icon()
                if isinstance(self.tasks[index.row()].reference, Character):
                    if role == Qt.DisplayRole:
                        return self.tasks[index.row()].reference.name
                    if role == Qt.DecorationRole:
                        return IconRegistry.character_icon()
        if index.column() == self.ColMessage:
            if role == Qt.DisplayRole:
                return self.tasks[index.row()].message
