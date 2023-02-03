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
import sys
from functools import partial

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import QScrollArea, QFrame, QApplication, QMainWindow, QLineEdit
from PyQt6.QtWidgets import QWidget
from qtanim import fade_in, fade_out
from qthandy import vbox, vspacer, hbox, gc, clear_layout

from src.main.python.plotlyst.core.template import SelectionItem
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.button import SecondaryActionPushButton
from src.main.python.plotlyst.view.widget.display import Icon
from src.main.python.plotlyst.view.widget.input import RemovalButton


class ListItemWidget(QWidget):
    deleted = pyqtSignal()

    def __init__(self, parent=None):
        super(ListItemWidget, self).__init__(parent)
        hbox(self)
        self._btnDrag = Icon()
        self._btnDrag.setIcon(IconRegistry.hashtag_icon())
        self._btnDrag.setIconSize(QSize(14, 14))

        self._lineEdit = QLineEdit()
        self._lineEdit.setPlaceholderText('Fill out...')

        self._btnRemoval = RemovalButton(self)
        self._btnRemoval.clicked.connect(self.deleted.emit)

        self.layout().addWidget(self._btnDrag)
        self.layout().addWidget(self._lineEdit)
        self.layout().addWidget(self._btnRemoval)


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

    def addItem(self, item: SelectionItem):
        wdg = ListItemWidget()
        wdg.deleted.connect(partial(self._deleteItemWidget, wdg))
        self._centralWidget.layout().insertWidget(self._centralWidget.layout().count() - 2, wdg)
        if self.isVisible():
            fade_in(wdg, 150)

    def clear(self):
        clear_layout(self._centralWidget, auto_delete=False)
        self._centralWidget.layout().addWidget(self._btnAdd)
        self._centralWidget.layout().addWidget(vspacer())

    def _addNewItem(self):
        item = SelectionItem('')
        self.addItem(item)

    def _deleteItemWidget(self, widget: ListItemWidget):
        def destroy():
            widget.setHidden(True)
            self._centralWidget.layout().removeWidget(widget)
            gc(widget)

        anim = fade_out(widget, 200)
        anim.finished.connect(destroy)


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            self.resize(500, 500)

            self.widget = ListView(self)
            self.setCentralWidget(self.widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
