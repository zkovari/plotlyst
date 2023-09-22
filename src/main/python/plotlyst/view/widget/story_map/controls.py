"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

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
from PyQt6.QtGui import QShowEvent
from overrides import overrides

from src.main.python.plotlyst.core.domain import DiagramNodeType, NODE_SUBTYPE_TOOL, NODE_SUBTYPE_COST
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.graphics import SecondarySelectorWidget


class StickerSelectorWidget(SecondarySelectorWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._btnComment = self.addItemTypeButton(DiagramNodeType.COMMENT,
                                                  IconRegistry.from_name('mdi.comment-text-outline'),
                                                  'Add new comment', 0, 0)
        self._btnTool = self.addItemTypeButton(DiagramNodeType.STICKER, IconRegistry.tool_icon('black', 'black'),
                                               'Add new tool',
                                               0, 1, subType=NODE_SUBTYPE_TOOL)
        self._btnCost = self.addItemTypeButton(DiagramNodeType.STICKER, IconRegistry.cost_icon('black', 'black'),
                                               'Add new cost',
                                               1, 0, subType=NODE_SUBTYPE_COST)

        self._btnComment.setChecked(True)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        self._btnComment.setChecked(True)
