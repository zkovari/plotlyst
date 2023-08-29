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
from typing import Optional

from PyQt6.QtCore import Qt, QEvent, QRect
from PyQt6.QtGui import QEnterEvent
from PyQt6.QtWidgets import QWidget, QTextEdit, QFrame
from overrides import overrides
from qthandy import hbox, margins, transparent
from qtmenu import MenuWidget
from typing_extensions import Optional

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.view.common import shadow, tool_btn
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.input import AutoAdjustableLineEdit, FontSizeSpinBox
from src.main.python.plotlyst.view.widget.story_map.items import MindMapNode, EventItem


class StickerEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = QTextEdit()
        self._text.setProperty('relaxed-white-bg', True)
        self._text.setProperty('rounded', True)
        self._text.setPlaceholderText('Leave a comment')

        hbox(self).addWidget(self._text)
        margins(self, left=3)

        self.setFixedSize(200, 200)

    def setText(self, text: str):
        self._text.setText(text)

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        self.setVisible(True)
        self._text.setFocus()

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        self.setHidden(True)


class TextLineEditorPopup(MenuWidget):

    def __init__(self, text: str, rect: QRect, parent=None):
        super().__init__(parent)
        transparent(self)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._lineEdit = AutoAdjustableLineEdit(defaultWidth=rect.width())
        self._lineEdit.setText(text)
        self.addWidget(self._lineEdit)

        self._lineEdit.editingFinished.connect(self.hide)

    @overrides
    def showEvent(self, QShowEvent):
        self._lineEdit.setFocus()

    def text(self) -> str:
        return self._lineEdit.text()


class EventItemEditor(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty('relaxed-white-bg', True)
        self.setProperty('rounded', True)
        shadow(self)
        hbox(self, spacing=6)

        self._item: Optional[MindMapNode] = None

        self._btnType = tool_btn(IconRegistry.from_name('mdi.square-rounded-outline'), 'Change type', transparent_=True)
        self._btnColor = tool_btn(IconRegistry.from_name('fa5s.circle', color=PLOTLYST_SECONDARY_COLOR), 'Change style',
                                  transparent_=True)
        self._btnBold = tool_btn(IconRegistry.from_name('fa5s.bold'), 'Bold', checkable=True, icon_resize=False,
                                 properties=['transparent-rounded-bg-on-hover', 'top-selector'])
        self._btnItalic = tool_btn(IconRegistry.from_name('fa5s.italic'), 'Italic',
                                   checkable=True, icon_resize=False,
                                   properties=['transparent-rounded-bg-on-hover', 'top-selector'])
        self._btnUnderline = tool_btn(IconRegistry.from_name('fa5s.underline'), 'Underline',
                                      checkable=True, icon_resize=False,
                                      properties=['transparent-rounded-bg-on-hover', 'top-selector'])

        self._sbFont = FontSizeSpinBox()

        self.layout().addWidget(self._btnType)
        self.layout().addWidget(self._btnColor)
        self.layout().addWidget(self._sbFont)
        self.layout().addWidget(self._btnBold)
        self.layout().addWidget(self._btnItalic)
        self.layout().addWidget(self._btnUnderline)

    def setItem(self, item: MindMapNode):
        self._item = item
        is_event = isinstance(self._item, EventItem)
        self._btnType.setVisible(is_event)
        self._btnBold.setVisible(is_event)
        self._btnItalic.setVisible(is_event)
        self._btnUnderline.setVisible(is_event)
