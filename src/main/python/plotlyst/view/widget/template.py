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
from typing import Optional, List, Any

import emoji
import qtawesome
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QDropEvent, QIcon, QMouseEvent, QDragMoveEvent, QDragEnterEvent
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QWidget, QGridLayout, QLineEdit, QLayoutItem, \
    QToolButton, QLabel, QSpinBox, QComboBox, QButtonGroup
from overrides import overrides

from src.main.python.plotlyst.core.domain import TemplateField, TemplateFieldType, SelectionItem, \
    ProfileTemplate, TemplateValue, ProfileElement
from src.main.python.plotlyst.view.common import emoji_font, spacer_widget


class _ProfileTemplateBase(QFrame):

    def __init__(self, profile: ProfileTemplate, parent=None):
        super().__init__(parent)
        self._profile = profile
        self.layout = QHBoxLayout(self)
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.layout.addWidget(self.scrollArea)

        self.widgets = []
        self._initGrid()

    def _initGrid(self):
        for el in self._profile.elements:
            widget = TemplateFieldWidget(el.field)
            self.widgets.append(widget)
            self.gridLayout.addWidget(widget, el.row, el.col)


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
    if item.icon:
        if item.icon.startswith('md'):
            return QIcon(qtawesome.icon(item.icon, color=item.icon_color, options=[{'scale_factor': 1.4}]))
        return QIcon(qtawesome.icon(item.icon, color=item.icon_color))
    else:
        return QIcon('')


class ButtonSelectionWidget(QWidget):

    def __init__(self, field: TemplateField, parent=None):
        super(ButtonSelectionWidget, self).__init__(parent)
        self.field = field

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.group = QButtonGroup()
        self.group.setExclusive(self.field.exclusive)
        self.buttons = []
        for i, item in enumerate(self.field.selections):
            btn = QToolButton()
            btn.setIcon(_icon(item))
            btn.setToolTip(item.text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            self.buttons.append(btn)
            self.layout.addWidget(btn)
            self.group.addButton(btn, i)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent):
        event.ignore()

    def value(self) -> List[int]:
        values = []
        for btn in self.group.buttons():
            if btn.isChecked():
                values.append(self.group.id(btn))
        return values

    def setValue(self, value: List[int]):
        for v in value:
            btn = self.group.button(v)
            if btn:
                btn.setChecked(True)


class TemplateFieldWidget(QFrame):
    def __init__(self, field: TemplateField, parent=None):
        super(TemplateFieldWidget, self).__init__(parent)
        self.field = field
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setProperty('mainFrame', True)

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

    @overrides
    def setEnabled(self, enabled: bool):
        self.wdgEditor.setEnabled(enabled)

    def select(self):
        self.setStyleSheet('QFrame[mainFrame=true] {border: 2px dashed #0496ff;}')

    def deselect(self):
        self.setStyleSheet('')

    def value(self) -> Any:
        if isinstance(self.wdgEditor, QSpinBox):
            return self.wdgEditor.value()
        if isinstance(self.wdgEditor, QLineEdit):
            return self.wdgEditor.text()
        if isinstance(self.wdgEditor, QComboBox):
            return self.wdgEditor.currentText()
        if isinstance(self.wdgEditor, ButtonSelectionWidget):
            return self.wdgEditor.value()

    def setValue(self, value: Any):
        if isinstance(self.wdgEditor, QSpinBox):
            self.wdgEditor.setValue(value)
        if isinstance(self.wdgEditor, QLineEdit):
            self.wdgEditor.setText(value)
        if isinstance(self.wdgEditor, QComboBox):
            self.wdgEditor.setCurrentText(value)
        if isinstance(self.wdgEditor, ButtonSelectionWidget):
            self.wdgEditor.setValue(value)

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


class ProfileTemplateEditor(_ProfileTemplateBase):
    MimeType: str = 'application/template-field'

    fieldSelected = pyqtSignal(TemplateField)
    fieldAdded = pyqtSignal(TemplateField)

    def __init__(self, profile: ProfileTemplate):
        super(ProfileTemplateEditor, self).__init__(profile)
        self.setAcceptDrops(True)
        self.setStyleSheet('QWidget {background-color: rgb(255, 255, 255);}')
        self._selected: Optional[TemplateFieldWidget] = None

        for w in self.widgets:
            w.setEnabled(False)

        for row in range(4):
            for col in range(2):
                if not self.gridLayout.itemAtPosition(row, col):
                    self.gridLayout.addWidget(placeholder(), row, col)

    def profile(self) -> ProfileTemplate:
        elements = []
        for i in range(self.gridLayout.count()):
            item = self.gridLayout.itemAt(i)
            if item and isinstance(item.widget(), TemplateFieldWidget):
                pos = self.gridLayout.getItemPosition(i)
                elements.append(ProfileElement(item.widget().field, row=pos[0], col=pos[1]))

        self._profile.elements = elements
        return self._profile

    @overrides
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(self.MimeType):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dragMoveEvent(self, event: QDragMoveEvent):
        index = self._get_index(event.pos())
        if index is None:
            return event.ignore()
        item = self.gridLayout.itemAt(index)
        if isinstance(item.widget(), TemplateFieldWidget):
            return event.ignore()

        event.accept()

    @overrides
    def dropEvent(self, event: QDropEvent):
        index = self._get_index(event.pos())
        if index is None:
            return

        field: TemplateField = pickle.loads(event.mimeData().data(self.MimeType))
        widget_to_drop = TemplateFieldWidget(field)
        widget_to_drop.setEnabled(False)
        pos = self.gridLayout.getItemPosition(index)
        item: QLayoutItem = self.gridLayout.takeAt(index)
        item.widget().deleteLater()
        self.gridLayout.addWidget(widget_to_drop, *pos)
        self.widgets.append(widget_to_drop)

        self.fieldAdded.emit(field)
        self._select(widget_to_drop)

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent):
        index = self._get_index(event.pos())
        if index is None:
            return
        item = self.gridLayout.itemAt(index)
        widget = item.widget()
        if isinstance(widget, TemplateFieldWidget):
            self._select(widget)

    def _select(self, widget: TemplateFieldWidget):
        if self._selected:
            self._selected.deselect()
        self._selected = widget
        self._selected.select()
        self.fieldSelected.emit(self._selected.field)

    def removeSelected(self):
        if self._selected:
            index = self.gridLayout.indexOf(self._selected)
            pos = self.gridLayout.getItemPosition(index)
            self.gridLayout.removeWidget(self._selected)
            self.gridLayout.addWidget(placeholder(), *pos)
            self.widgets.remove(self._selected)
            self._selected.deleteLater()
            self._selected = None

    def _get_index(self, pos: QPoint) -> Optional[int]:
        for i in range(self.gridLayout.count()):
            if self.gridLayout.itemAt(i).geometry().contains(pos):
                return i


class ProfileTemplateView(_ProfileTemplateBase):
    def __init__(self, profile: ProfileTemplate):
        super(ProfileTemplateView, self).__init__(profile)

        self.setStyleSheet('QWidget {background-color: rgb(255, 255, 255);}')
        self._selected: Optional[TemplateFieldWidget] = None

    def values(self) -> List[TemplateValue]:
        values: List[TemplateValue] = []
        for widget in self.widgets:
            values.append(TemplateValue(id=widget.field.id, value=widget.value()))

        return values

    def setValues(self, values: List[TemplateValue]):
        ids = {}
        for value in values:
            ids[str(value.id)] = value.value

        for widget in self.widgets:
            if str(widget.field.id) in ids.keys():
                widget.setValue(ids[str(widget.field.id)])
