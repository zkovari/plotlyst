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
from abc import abstractmethod
from functools import partial
from typing import Optional, Any, List

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QEvent, QObject, QPoint
from PyQt6.QtWidgets import QScrollArea, QFrame, QLineEdit
from PyQt6.QtWidgets import QWidget
from overrides import overrides
from qtanim import fade_in
from qthandy import vbox, vspacer, hbox, clear_layout, retain_when_hidden, margins, gc, translucent
from qthandy.filter import DragEventFilter, DropEventFilter, ObjectReferenceMimeData

from src.main.python.plotlyst.view.common import fade_out_and_gc
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.input import RemovalButton

LIST_ITEM_MIME_TYPE = 'application/list-item'


class ListItemWidget(QWidget):
    deleted = pyqtSignal()
    changed = pyqtSignal()
    dragStarted = pyqtSignal()
    dragFinished = pyqtSignal()

    def __init__(self, item: Any, parent=None):
        super(ListItemWidget, self).__init__(parent)
        hbox(self, spacing=1)
        margins(self, left=0)
        self._item = item
        self._btnDrag = Icon()
        self._btnDrag.setIcon(IconRegistry.hashtag_icon('grey'))
        self._btnDrag.setIconSize(QSize(12, 12))
        self._btnDrag.setCursor(Qt.CursorShape.OpenHandCursor)

        self._lineEdit = QLineEdit()
        self._lineEdit.setPlaceholderText('Fill out...')
        self._lineEdit.textChanged.connect(self._textChanged)

        self._btnRemoval = RemovalButton(self)
        self._btnRemoval.clicked.connect(self.deleted.emit)

        self.layout().addWidget(self._btnDrag)
        self.layout().addWidget(self._lineEdit)
        self.layout().addWidget(self._btnRemoval)
        retain_when_hidden(self._btnDrag)
        retain_when_hidden(self._btnRemoval)
        self._btnDrag.setHidden(True)
        self._btnRemoval.setHidden(True)

        self._btnDrag.installEventFilter(
            DragEventFilter(self, LIST_ITEM_MIME_TYPE, dataFunc=lambda x: self.item(), hideTarget=True,
                            grabbed=self._lineEdit, startedSlot=self.dragStarted.emit,
                            finishedSlot=self.dragFinished.emit))

        self.installEventFilter(self)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            self._btnDrag.setVisible(True)
            self._btnRemoval.setVisible(True)
        elif event.type() == QEvent.Type.Leave:
            self._btnDrag.setHidden(True)
            self._btnRemoval.setHidden(True)
        return super(ListItemWidget, self).eventFilter(watched, event)

    def item(self) -> Any:
        return self._item

    def activate(self):
        self._lineEdit.setFocus()

    def _textChanged(self, text: str):
        self.changed.emit()


class ListView(QScrollArea):

    def __init__(self, parent=None):
        super(ListView, self).__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._centralWidget = QWidget(self)
        self.setWidget(self._centralWidget)
        vbox(self._centralWidget, spacing=0)

        self._btnAdd = SecondaryActionPushButton('Add new')
        self._centralWidget.layout().addWidget(self._btnAdd)
        self._centralWidget.layout().addWidget(vspacer())

        self._btnAdd.clicked.connect(self._addNewItem)

        self._dragPlaceholder: Optional[ListItemWidget] = None
        self._dragged: Optional[ListItemWidget] = None
        self._toBeRemoved = False

    def centralWidget(self) -> QWidget:
        return self._centralWidget

    def addItem(self, item: Any):
        wdg = self.__newItemWidget(item)

        self._centralWidget.layout().insertWidget(self._centralWidget.layout().count() - 2, wdg)
        if self.isVisible():
            anim = fade_in(wdg, 150)
            anim.finished.connect(wdg.activate)

    def clear(self):
        clear_layout(self._centralWidget, auto_delete=False)
        self._centralWidget.layout().addWidget(self._btnAdd)
        self._centralWidget.layout().addWidget(vspacer())

    def widgets(self) -> List[ListItemWidget]:
        wdgs = []
        for i in range(self._centralWidget.layout().count() - 2):
            wdg = self._centralWidget.layout().itemAt(i).widget()
            if wdg is self._dragPlaceholder or wdg is self._dragged:
                continue
            wdgs.append(wdg)

        return wdgs

    @abstractmethod
    def _addNewItem(self):
        pass

    @abstractmethod
    def _listItemWidgetClass(self):
        pass

    def _deleteItemWidget(self, widget: ListItemWidget):
        fade_out_and_gc(self._centralWidget, widget)

    def _dragStarted(self, widget: ListItemWidget):
        self._dragged = widget
        self._dragPlaceholder = ListItemWidget(widget.item(), self)
        margins(self._dragPlaceholder, left=3)
        translucent(self._dragPlaceholder)
        self._dragPlaceholder.setHidden(True)
        self._dragPlaceholder.setAcceptDrops(True)
        self._dragPlaceholder.installEventFilter(
            DropEventFilter(self._dragPlaceholder, mimeTypes=[LIST_ITEM_MIME_TYPE], droppedSlot=self._dropped))

    def _dragFinished(self, widget: ListItemWidget):
        if self._dragPlaceholder:
            self._dragPlaceholder.setHidden(True)
            self._centralWidget.layout().removeWidget(self._dragPlaceholder)
            gc(self._dragPlaceholder)
            self._dragPlaceholder = None

        self._dragged = None
        if self._toBeRemoved:
            widget.setHidden(True)
            self._centralWidget.layout().removeWidget(widget)
            gc(widget)

        self._toBeRemoved = False

    def _dragMoved(self, widget: ListItemWidget, edge: Qt.Edge, _: QPoint):
        self._dragPlaceholder.setVisible(True)
        i = self._centralWidget.layout().indexOf(widget)
        if edge == Qt.Edge.TopEdge:
            self._centralWidget.layout().insertWidget(i, self._dragPlaceholder)
        else:
            self._centralWidget.layout().insertWidget(i + 1, self._dragPlaceholder)

    def _dropped(self, mimeData: ObjectReferenceMimeData):
        wdg = self.__newItemWidget(mimeData.reference())
        self._centralWidget.layout().replaceWidget(self._dragPlaceholder, wdg)
        gc(self._dragPlaceholder)
        self._dragPlaceholder = None

        self._toBeRemoved = True

    def __newItemWidget(self, item: Any):
        wdg = self._listItemWidgetClass()(item)
        wdg.deleted.connect(partial(self._deleteItemWidget, wdg))
        wdg.dragStarted.connect(partial(self._dragStarted, wdg))
        wdg.dragFinished.connect(partial(self._dragFinished, wdg))
        wdg.setAcceptDrops(True)
        wdg.installEventFilter(
            DropEventFilter(self, mimeTypes=[LIST_ITEM_MIME_TYPE], motionDetection=Qt.Orientation.Vertical,
                            motionSlot=partial(self._dragMoved, wdg), droppedSlot=self._dropped))

        return wdg
