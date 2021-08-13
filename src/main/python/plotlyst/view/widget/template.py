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
import pickle
from typing import Optional

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QWidget, QGridLayout, QLineEdit, QLayoutItem, \
    QToolButton
from overrides import overrides

from src.main.python.plotlyst.core.domain import TemplateField


class TemplateProfile(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout(self)
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.layout.addWidget(self.scrollArea)
        self.setStyleSheet('QFrame#TemplateProfile {background-color: white;}')


def placeholder() -> QWidget:
    frame = QFrame()
    layout = QHBoxLayout(frame)
    frame.setLayout(layout)

    btn = QToolButton()
    btn.setIcon(qtawesome.icon('ei.plus-sign', color='grey'))
    btn.setText('<Drop here>')
    btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    btn.setStyleSheet('''
        background-color: rgb(255, 255, 255);
        border: 0px;
        color: grey;''')
    layout.addWidget(btn)
    return frame


class TemplateProfileEditor(TemplateProfile):
    MimeType: str = 'application/template-field'

    def __init__(self):
        super(TemplateProfileEditor, self).__init__()
        self.setAcceptDrops(True)

        for row in range(3):
            for col in range(2):
                self.gridLayout.addWidget(placeholder(), row, col)

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(self.MimeType):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dropEvent(self, event: QDropEvent):
        if not event.source().geometry().contains(event.pos()):
            index = self.get_index(event.pos())
            if index is None:
                return

            field: TemplateField = pickle.loads(event.mimeData().data(self.MimeType))
            widget_to_drop = QLineEdit()
            widget_to_drop.setPlaceholderText(field.name)
            pos = self.gridLayout.getItemPosition(index)
            item: QLayoutItem = self.gridLayout.takeAt(index)
            item.widget().deleteLater()
            self.gridLayout.addWidget(widget_to_drop, *pos)

    def get_index(self, pos) -> Optional[int]:
        for i in range(self.gridLayout.count()):
            if self.gridLayout.itemAt(i).geometry().contains(pos):
                return i


class TemplateProfileView(TemplateProfile):
    pass
