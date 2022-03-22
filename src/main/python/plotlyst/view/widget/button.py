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
from functools import partial

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QPushButton, QSizePolicy

from src.main.python.plotlyst.core.domain import SelectionItem
from src.main.python.plotlyst.view.common import OpacityEventFilter
from src.main.python.plotlyst.view.icons import IconRegistry


class SelectionItemPushButton(QPushButton):
    itemClicked = pyqtSignal(SelectionItem)

    def __init__(self, parent=None):
        super(SelectionItemPushButton, self).__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def setSelectionItem(self, item: SelectionItem):
        self.setText(item.text)
        if item.icon:
            self.setIcon(IconRegistry.from_name(item.icon, item.icon_color))

        self.clicked.connect(partial(self.itemClicked.emit, item))


class SecondaryActionPushButton(QPushButton):
    def __init__(self, parent=None):
        super(SecondaryActionPushButton, self).__init__(parent)
        self.setStyleSheet('''
            QPushButton {
                border: 1px dashed grey;
                border-radius: 6px;
                color: grey;
            }
            QPushButton:pressed {
                border: 1px solid grey;
            }
            QPushButton:checked {
                border: 2px solid black;
            }
        ''')
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        self.installEventFilter(OpacityEventFilter(enterOpacity=0.9, leaveOpacity=0.7, parent=self))
