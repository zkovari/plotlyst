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

import emoji
import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon, QMouseEvent
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QWidget, QGridLayout, QLineEdit, QLayoutItem, \
    QToolButton, QLabel, QSpinBox, QComboBox, QButtonGroup
from overrides import overrides

from src.main.python.plotlyst.core.domain import TemplateField, TemplateFieldType, SelectionItem
from src.main.python.plotlyst.view.common import emoji_font, spacer_widget


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


def _icon(item: SelectionItem) -> QIcon:
    return QIcon(qtawesome.icon(item.icon)) if item.icon else QIcon('')


class ButtonSelectionWidget(QWidget):

    def __init__(self, field: TemplateField, parent=None):
        super(ButtonSelectionWidget, self).__init__(parent)
        self.field = field

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.group = QButtonGroup()
        self.buttons = []
        for item in self.field.selections:
            btn = QToolButton()
            btn.setIcon(_icon(item))
            btn.setToolTip(item.text)
            btn.setCheckable(True)
            self.buttons.append(btn)
            self.layout.addWidget(btn)
            if self.field.exclusive:
                self.group.addButton(btn)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent):
        event.ignore()


class TemplateFieldWidget(QWidget):
    def __init__(self, field: TemplateField, parent=None):
        super(TemplateFieldWidget, self).__init__(parent)
        self.field = field
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        if self.field.emoji:
            self.lblEmoji = QLabel()
            self.lblEmoji.setFont(emoji_font())
            self.lblEmoji.setText(emoji.emojize(self.field.emoji))
            self.layout.addWidget(self.lblEmoji)

        self.lblName = QLabel()
        self.lblName.setText(self.field.name)
        self.layout.addWidget(self.lblName)

        self.wdgEditor = self._fieldWidget()
        self.layout.addWidget(self.wdgEditor)

        if self.field.compact:
            self.layout.addWidget(spacer_widget())

    def setReadOnly(self, readOnly: bool):
        self.wdgEditor.setDisabled(readOnly)
        # if isinstance(self.wdgEditor, (QLineEdit, QSpinBox)):
        #     self.wdgEditor.setReadOnly(readOnly)
        # elif isinstance(self.wdgEditor, QComboBox):
        #     for i in range(self.wdgEditor.count()):
        #         item = self.wdgEditor.model().item(i)
        #         if readOnly:
        #             item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        #         else:
        #             item.setFlags(item.flags() | Qt.ItemIsEnabled)

    # @overrides
    # def mouseReleaseEvent(self, event: QMouseEvent):
    #     print(event.pos())

    def _fieldWidget(self) -> QWidget:
        if self.field.type == TemplateFieldType.NUMERIC:
            widget = QSpinBox()
            widget.setMinimum(self.field.min_value)
            widget.setMaximum(self.field.max_value)
        elif self.field.type == TemplateFieldType.TEXT_SELECTION:
            widget = QComboBox()
            for item in self.field.selections:
                widget.addItem(_icon(item), item.text)
        elif self.field.type == TemplateFieldType.BUTTON_SELECTION:
            widget = ButtonSelectionWidget(self.field)
        else:
            widget = QLineEdit()
            widget.setPlaceholderText(self.field.placeholder)

        return widget


class TemplateProfileEditor(TemplateProfile):
    MimeType: str = 'application/template-field'

    def __init__(self):
        super(TemplateProfileEditor, self).__init__()
        self.setAcceptDrops(True)
        self.setStyleSheet('QWidget {background-color: rgb(255, 255, 255);}')

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
        index = self.get_index(event.pos())
        if index is None:
            return

        field: TemplateField = pickle.loads(event.mimeData().data(self.MimeType))
        widget_to_drop = TemplateFieldWidget(field)
        widget_to_drop.setReadOnly(True)
        pos = self.gridLayout.getItemPosition(index)
        item: QLayoutItem = self.gridLayout.takeAt(index)
        item.widget().deleteLater()
        self.gridLayout.addWidget(widget_to_drop, *pos)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent):
        print(event.pos())

    def get_index(self, pos) -> Optional[int]:
        for i in range(self.gridLayout.count()):
            if self.gridLayout.itemAt(i).geometry().contains(pos):
                return i


class TemplateProfileView(TemplateProfile):
    pass
