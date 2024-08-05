"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
from enum import Enum, auto
from typing import Any

from PyQt6.QtGui import QUndoCommand
from PyQt6.QtWidgets import QGraphicsItem
from overrides import overrides


class MergeableCommandType(Enum):
    PEN_WIDTH = auto()


class MergeableGraphicsItemCommand(QUndoCommand):
    def __init__(self, type: MergeableCommandType, item: QGraphicsItem, func, old: Any, new: Any, parent=None):
        super().__init__(parent)
        self.type = type
        self.item = item
        self.func = func
        self.old = old
        self.new = new

    @overrides
    def id(self) -> int:
        return self.type.value

    @overrides
    def mergeWith(self, other: 'MergeableGraphicsItemCommand') -> bool:
        if self.type == other.type and self.item is other.item:
            self.new = other.new
            return True
        return False

    @overrides
    def redo(self) -> None:
        self.func(self.new)

    @overrides
    def undo(self) -> None:
        self.func(self.old)


class GraphicsItemCommand(QUndoCommand):
    def __init__(self, item: QGraphicsItem, func, old: Any, new: Any, parent=None):
        super().__init__(parent)
        self.item = item
        self.func = func
        self.old = old
        self.new = new

    @overrides
    def redo(self) -> None:
        self.func(self.new)

    @overrides
    def undo(self) -> None:
        self.func(self.old)
