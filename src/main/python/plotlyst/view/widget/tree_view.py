"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from typing import Optional

from PyQt5 import QtGui
from PyQt5.QtCore import QModelIndex, QSize, QRect
from PyQt5.QtWidgets import QTreeView, QStyledItemDelegate, QStyleOptionViewItem
from overrides import overrides

from src.main.python.plotlyst.view.icons import IconRegistry


class ActionBasedTreeView(QTreeView):

    def __init__(self, parent=None):
        super(ActionBasedTreeView, self).__init__(parent)
        # self._delegate = ActionBasedTreeViewDelegate()
        # self.setItemDelegate(self._delegate)

    # @overrides
    # def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
    #     scroll_bar = self.verticalScrollBar().width()
    #     if 5 < event.pos().x() < self.rect().width() - scroll_bar - 5:
    #         index = self.indexAt(event.pos())
    #         self._delegate.indexToPaint = index
    #     else:
    #         self._delegate.indexToPaint = None
    #
    #     self.update()
    #     super(ActionBasedTreeView, self).mouseMoveEvent(event)
    #
    # @overrides
    # def leaveEvent(self, event: QtCore.QEvent) -> None:
    #     self._delegate.indexToPaint = None
    #     self.update()
    #
    #     super(ActionBasedTreeView, self).leaveEvent(event)


class ActionBasedTreeViewDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(ActionBasedTreeViewDelegate, self).__init__(parent)
        self.indexToPaint: Optional[QModelIndex] = None

    @overrides
    def paint(self, painter: QtGui.QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super(ActionBasedTreeViewDelegate, self).paint(painter, option, index)
        if self.indexToPaint:
            if self.indexToPaint.row() == index.row() and index.column() == 1:
                rect: QRect = option.rect
                # painter.drawPixmap(option.rect, IconRegistry.plus_icon().pixmap(QSize(16, 16)))
                painter.drawPixmap(rect.x(), rect.y(), IconRegistry.plus_icon().pixmap(QSize(16, 16)))
