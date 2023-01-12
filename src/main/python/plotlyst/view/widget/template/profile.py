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
import pickle
from functools import partial
from typing import Optional, List, Dict, Tuple

import emoji
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QObject
from PyQt6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent
from PyQt6.QtWidgets import QWidget, QToolButton, QScrollArea, QFrame, \
    QGridLayout, QHBoxLayout, QLayoutItem, QPushButton, QSpacerItem, QSizePolicy
from overrides import overrides
from qthandy import vbox, gc

from src.main.python.plotlyst.core.domain import TemplateValue
from src.main.python.plotlyst.core.template import ProfileTemplate, TemplateField, HAlignment, VAlignment, \
    ProfileElement
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.template.base import TemplateWidgetBase, TemplateDisplayWidget, \
    EditableTemplateWidget
from src.main.python.plotlyst.view.widget.template.factory import TemplateFieldWidgetFactory
from src.main.python.plotlyst.view.widget.template.impl import HeaderTemplateDisplayWidget, TextSelectionWidget


class _PlaceHolder(QFrame):
    def __init__(self):
        super(_PlaceHolder, self).__init__()
        layout = QHBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(2, 2, 1, 2)
        self.setLayout(layout)

        self.btn = QToolButton()
        self.btn.setIcon(IconRegistry.from_name('ei.plus-sign', color='lightgrey'))
        self.btn.setText('<Drop here>')
        self.btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.btn.setStyleSheet('''
                background-color: rgb(255, 255, 255);
                border: 0px;
                color: lightgrey;''')
        layout.addWidget(self.btn)


def is_placeholder(widget: QWidget) -> bool:
    return isinstance(widget, _PlaceHolder) or isinstance(widget.parent(), _PlaceHolder)


class _ProfileTemplateBase(QWidget):

    def __init__(self, profile: ProfileTemplate, editor_mode: bool = False, disabled_template_headers=None,
                 parent=None):
        super().__init__(parent)
        self._profile = profile
        self._disabled_template_headers: Dict[
            str, bool] = disabled_template_headers if disabled_template_headers else {}
        self.layout = vbox(self)
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.scrollAreaWidgetContents = QWidget()
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setSpacing(1)
        self.gridLayout.setContentsMargins(2, 0, 2, 0)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.layout.addWidget(self.scrollArea)

        self._spacer_item = QSpacerItem(20, 50, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self.widgets: List[TemplateWidgetBase] = []
        self._headers: List[Tuple[int, HeaderTemplateDisplayWidget]] = []
        self._initGrid(editor_mode)

    def _initGrid(self, editor_mode: bool):
        self.widgets.clear()
        self._headers.clear()

        for el in self._profile.elements:
            widget = TemplateFieldWidgetFactory.widget(el.field, self)
            if el.margins:
                widget.setContentsMargins(el.margins.left, el.margins.top, el.margins.right, el.margins.bottom)
            self.widgets.append(widget)
            self.gridLayout.addWidget(widget, el.row, el.col, el.row_span, el.col_span,
                                      el.h_alignment.value | el.v_alignment.value)

            if isinstance(widget, HeaderTemplateDisplayWidget):
                self._headers.append((el.row, widget))
            else:
                if self._headers:
                    self._headers[-1][1].attachWidget(widget)

        for _, header in self._headers:
            header.updateProgress()
            header.setHeaderEnabled(self._disabled_template_headers.get(str(header.field.id), header.field.enabled))
            header.headerEnabledChanged.connect(partial(self._headerEnabledChanged, header.field))

        self._addSpacerToEnd()

    def _addSpacerToEnd(self):
        self.gridLayout.addItem(self._spacer_item,
                                self.gridLayout.rowCount(), 0)
        self.gridLayout.setRowStretch(self.gridLayout.rowCount() - 1, 1)

    def values(self) -> List[TemplateValue]:
        values: List[TemplateValue] = []
        for widget in self.widgets:
            if isinstance(widget, TemplateDisplayWidget):
                continue
            values.append(TemplateValue(id=widget.field.id, value=widget.value(), notes=widget.notes()))

        return values

    def setValues(self, values: List[TemplateValue]):
        ids = {}
        for value in values:
            ids[str(value.id)] = value

        for widget in self.widgets:
            if isinstance(widget, EditableTemplateWidget):
                if str(widget.field.id) in ids.keys():
                    value = ids[str(widget.field.id)]
                    widget.setValue(value.value)
                    if value.notes:
                        widget.setNotes(value.notes)

    def clearValues(self):
        for wdg in self.widgets:
            if isinstance(wdg, EditableTemplateWidget):
                wdg.clear()

    def _headerEnabledChanged(self, header: TemplateField, enabled: bool):
        pass


class ProfileTemplateEditor(_ProfileTemplateBase):
    MimeType: str = 'application/template-field'

    fieldSelected = pyqtSignal(TemplateField)
    placeholderSelected = pyqtSignal()
    fieldAdded = pyqtSignal(TemplateField)

    def __init__(self, profile: ProfileTemplate):
        super(ProfileTemplateEditor, self).__init__(profile, editor_mode=True)
        self.setAcceptDrops(True)
        self.setStyleSheet('QWidget {background-color: rgb(255, 255, 255);}')
        self._selected: Optional[TemplateWidgetBase] = None
        self._target_to_drop: Optional[QWidget] = None

        for w in self.widgets:
            w.setEnabled(False)
            w.setAcceptDrops(True)
            self._installEventFilter(w)

        self.gridLayout.removeItem(self._spacer_item)
        for row in range(max(6, self.gridLayout.rowCount() + 1)):
            for col in range(2):
                if not self.gridLayout.itemAtPosition(row, col):
                    self._addPlaceholder(row, col)

    def profile(self) -> ProfileTemplate:
        elements = []
        for i in range(self.gridLayout.count()):
            item = self.gridLayout.itemAt(i)
            if item and isinstance(item.widget(), EditableTemplateWidget):
                pos = self.gridLayout.getItemPosition(i)
                item = self.gridLayout.itemAtPosition(pos[0], pos[1])
                if item.alignment() & Qt.AlignmentFlag.AlignRight:
                    h_alignment = HAlignment.RIGHT
                elif item.alignment() & Qt.AlignmentFlag.AlignLeft:
                    h_alignment = HAlignment.LEFT
                elif item.alignment() & Qt.AlignmentFlag.AlignHCenter:
                    h_alignment = HAlignment.CENTER
                elif item.alignment() & Qt.AlignmentFlag.AlignJustify:
                    h_alignment = HAlignment.JUSTIFY
                else:
                    h_alignment = HAlignment.DEFAULT

                if item.alignment() & Qt.AlignmentFlag.AlignTop:
                    v_alignment = VAlignment.TOP
                elif item.alignment() & Qt.AlignmentFlag.AlignBottom:
                    v_alignment = VAlignment.BOTTOM
                else:
                    v_alignment = VAlignment.CENTER

                elements.append(
                    ProfileElement(item.widget().field, row=pos[0], col=pos[1], row_span=pos[2], col_span=pos[3],
                                   h_alignment=h_alignment, v_alignment=v_alignment))

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
        if not self._target_to_drop:
            event.ignore()
            return
        if is_placeholder(self._target_to_drop):
            event.accept()
        else:
            event.ignore()

    @overrides
    def dropEvent(self, event: QDropEvent):
        if not self._target_to_drop:
            event.ignore()
            return

        if isinstance(self._target_to_drop, _PlaceHolder):
            placeholder = self._target_to_drop
        elif isinstance(self._target_to_drop.parent(), _PlaceHolder):
            placeholder = self._target_to_drop.parent()
        else:
            event.ignore()
            return
        index = self.gridLayout.indexOf(placeholder)

        field: TemplateField = pickle.loads(event.mimeData().data(self.MimeType))
        widget_to_drop = TemplateFieldWidgetFactory.widget(field)
        widget_to_drop.setEnabled(False)
        pos = self.gridLayout.getItemPosition(index)
        item: QLayoutItem = self.gridLayout.takeAt(index)
        gc(item.widget())
        self.gridLayout.addWidget(widget_to_drop, *pos)
        self._installEventFilter(widget_to_drop)

        self.widgets.append(widget_to_drop)

        self.fieldAdded.emit(field)
        self._select(widget_to_drop)

        if pos[0] == self.gridLayout.rowCount() - 1:
            self._addPlaceholder(pos[0] + 1, 0)
            self._addPlaceholder(pos[0] + 1, 1)
            self.gridLayout.update()

        event.accept()

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonRelease:
            if isinstance(watched, (QToolButton, QPushButton)):
                self._select(watched.parent())
            else:
                self._select(watched)
        elif event.type() == QEvent.Type.DragEnter:
            self._target_to_drop = watched
            self.dragMoveEvent(event)
        elif event.type() == QEvent.Type.Drop:
            self.dropEvent(event)
            self._target_to_drop = None
        return super().eventFilter(watched, event)

    def _select(self, widget: TemplateWidgetBase):
        if self._selected:
            self._selected.deselect()
        if is_placeholder(widget):
            self._selected = None
            self.placeholderSelected.emit()
            return
        self._selected = widget
        self._selected.select()
        self.fieldSelected.emit(self._selected.field)

    def removeSelected(self):
        if self._selected:
            index = self.gridLayout.indexOf(self._selected)
            pos = self.gridLayout.getItemPosition(index)
            self.gridLayout.removeWidget(self._selected)
            self._addPlaceholder(pos[0], pos[1])
            self.widgets.remove(self._selected)
            gc(self._selected)
            self._selected = None

    def setShowLabelForSelected(self, enabled: bool):
        if self._selected:
            self._selected.lblName.setVisible(enabled)

    def updateLabelForSelected(self, text: str):
        if self._selected:
            self._selected.lblName.setText(text)

    def updateEmojiForSelected(self, text: str):
        if self._selected:
            self._selected.updateEmoji(emoji.emojize(text))

    def _installEventFilter(self, widget: TemplateWidgetBase):
        widget.installEventFilter(self)
        if isinstance(widget, TemplateWidgetBase) and not isinstance(widget, TemplateDisplayWidget) and isinstance(
                widget.wdgEditor, TextSelectionWidget):
            widget.wdgEditor.installEventFilter(self)

    def _addPlaceholder(self, row: int, col: int):
        _placeholder = _PlaceHolder()
        self.gridLayout.addWidget(_placeholder, row, col)
        _placeholder.setAcceptDrops(True)
        _placeholder.btn.setAcceptDrops(True)
        _placeholder.installEventFilter(self)
        _placeholder.btn.installEventFilter(self)


class ProfileTemplateView(_ProfileTemplateBase):
    def __init__(self, values: List[TemplateValue], profile: ProfileTemplate, disabled_template_headers):
        super().__init__(profile, disabled_template_headers=disabled_template_headers)
        self.setProperty('mainFrame', True)
        self.setValues(values)
