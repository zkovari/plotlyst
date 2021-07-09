from typing import Optional

from PyQt5 import QtGui
from PyQt5.QtCore import QModelIndex, QSize, QRect
from PyQt5.QtWidgets import QTreeView, QStyledItemDelegate, QStyleOptionViewItem
from overrides import overrides

from novel_outliner.view.icons import IconRegistry


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
