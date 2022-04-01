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
from PyQt5.QtWidgets import QPushButton, QSizePolicy, QToolButton, QAbstractButton, QLabel
from overrides import overrides
from qthandy import hbox

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
        self.toggled.connect(self._toggled)

    def _toggled(self, checked: bool):
        font = self.font()
        font.setBold(checked)
        self.setFont(font)


class _SecondaryActionButton(QAbstractButton):
    def __init__(self, parent=None):
        super(_SecondaryActionButton, self).__init__(parent)
        self.initStyleSheet()
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        self.installEventFilter(OpacityEventFilter(leaveOpacity=0.7, parent=self))

    def initStyleSheet(self, border_color: str = 'grey', border_color_checked: str = 'black'):
        self.setStyleSheet(f'''
                {self.__class__.__name__} {{
                    border: 2px dashed {border_color};
                    border-radius: 6px;
                    color: grey;
                    padding: 2px;
                }}
                {self.__class__.__name__}:pressed {{
                    border: 2px solid {border_color};
                }}
                {self.__class__.__name__}:checked {{
                    border: 2px solid {border_color_checked};
                }}
            ''')

    def setBorderColor(self, color_name: str):
        self.initStyleSheet(color_name)
        self.update()


class SecondaryActionToolButton(QToolButton, _SecondaryActionButton):
    pass


class SecondaryActionPushButton(QPushButton, _SecondaryActionButton):
    pass


class WordWrappedPushButton(QPushButton):
    def __init__(self, parent=None):
        super(WordWrappedPushButton, self).__init__(parent)
        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.NoTextInteraction)
        self.label.setAlignment(Qt.AlignCenter)
        hbox(self, 0, 0).addWidget(self.label, alignment=Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)

    @overrides
    def setText(self, text: str):
        self.label.setText(text)
        self.setFixedHeight(self.label.height() + 5)
