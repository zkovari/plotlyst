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

from PyQt5.QtCore import QModelIndex, Qt
from anytree import Node
from overrides import overrides

from src.main.python.plotlyst.core.domain import VERY_UNHAPPY
from src.main.python.plotlyst.model.tree_model import TreeItemModel
from src.main.python.plotlyst.view.icons import IconRegistry


class CharacterReportNode(Node):
    pass


class CharacterArcReportNode(Node):
    pass


class ConflictReportNode(Node):
    pass


class PlotReportNode(Node):
    pass


class ReportsTreeModel(TreeItemModel):
    def __init__(self, parent=None):
        super(ReportsTreeModel, self).__init__(parent)
        char_node = CharacterReportNode('Characters', self.root)
        CharacterArcReportNode('Emotional Arc', char_node)
        ConflictReportNode('Conflicts', self.root)
        PlotReportNode('Plot', self.root)

    @overrides
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        node = index.internalPointer()
        if role == Qt.DecorationRole:
            if isinstance(node, CharacterReportNode):
                return IconRegistry.character_icon()
            if isinstance(node, CharacterArcReportNode):
                return IconRegistry.emotion_icon_from_feeling(VERY_UNHAPPY)
            if isinstance(node, ConflictReportNode):
                return IconRegistry.conflict_icon()
            if isinstance(node, PlotReportNode):
                return IconRegistry.plot_icon()

        return super(ReportsTreeModel, self).data(index, role)
