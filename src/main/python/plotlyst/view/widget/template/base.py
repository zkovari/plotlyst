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
from typing import Any

import emoji
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, \
    QLabel, QSizePolicy
from overrides import overrides

from src.main.python.plotlyst.core.template import TemplateField
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.view.common import emoji_font


class TemplateWidgetBase(QFrame):
    valueFilled = pyqtSignal()
    valueReset = pyqtSignal()

    def __init__(self, field: TemplateField, parent=None):
        super(TemplateWidgetBase, self).__init__(parent)
        self.field = field
        self.setProperty('mainFrame', True)

    def select(self):
        self.setStyleSheet('QFrame[mainFrame=true] {border: 2px dashed #0496ff;}')

    def deselect(self):
        self.setStyleSheet('')

    def notes(self) -> str:
        if self.field.has_notes:
            return self._notesEditor.toMarkdown()
        return ''

    def setNotes(self, notes: str):
        if self.field.has_notes:
            self._notesEditor.setMarkdown(notes)


class TemplateDisplayWidget(TemplateWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super(TemplateDisplayWidget, self).__init__(field, parent)


class EditableTemplateWidget(TemplateWidgetBase):
    def __init__(self, field: TemplateField, parent=None):
        super().__init__(field, parent)

    @abstractmethod
    def value(self) -> Any:
        pass

    @abstractmethod
    def setValue(self, value: Any):
        pass


class TemplateFieldWidgetBase(EditableTemplateWidget):
    def __init__(self, field: TemplateField, parent=None):
        super(TemplateFieldWidgetBase, self).__init__(field, parent)
        self.lblEmoji = QLabel(self)
        self.lblEmoji.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.lblEmoji.setToolTip(field.description if field.description else field.placeholder)
        self.lblName = QLabel(self)
        self.lblName.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.lblName.setText(self.field.name)
        self.lblName.setToolTip(field.description if field.description else field.placeholder)

        if self.field.emoji:
            self.updateEmoji(emoji.emojize(self.field.emoji))
        else:
            self.lblEmoji.setHidden(True)

        if not field.show_label:
            self.lblName.setHidden(True)

        if app_env.is_mac():
            self._boxSpacing = 1
            self._boxMargin = 0
        else:
            self._boxSpacing = 3
            self._boxMargin = 1

    @overrides
    def setEnabled(self, enabled: bool):
        if not self.layout():
            return
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget():
                item.widget().setEnabled(enabled)

    def updateEmoji(self, emoji: str):
        if app_env.is_windows():
            emoji_size = 14
        else:
            emoji_size = 20

        self.lblEmoji.setFont(emoji_font(emoji_size))
        self.lblEmoji.setText(emoji)
        self.lblEmoji.setVisible(True)

    def clear(self):
        self.wdgEditor.clear()


class ComplexTemplateWidgetBase(EditableTemplateWidget):
    pass
