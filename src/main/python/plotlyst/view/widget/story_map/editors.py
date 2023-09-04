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
from PyQt6.QtWidgets import QWidget, QTextEdit
from overrides import overrides
from qthandy import hbox, margins, transparent, vline
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.view.common import tool_btn
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.graphics import BaseItemEditor
from src.main.python.plotlyst.view.widget.input import AutoAdjustableLineEdit, FontSizeSpinBox
from src.main.python.plotlyst.view.widget.story_map.controls import EventSelectorWidget
from src.main.python.plotlyst.view.widget.story_map.items import EventItem, ItemType


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


class EventItemEditor(BaseItemEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._item: Optional[EventItem] = None

        self._btnType = tool_btn(IconRegistry.from_name('mdi.square-rounded-outline'), 'Change type', transparent_=True)
        self._btnColor = tool_btn(IconRegistry.from_name('fa5s.circle', color=PLOTLYST_SECONDARY_COLOR), 'Change style',
                                  transparent_=True)
        self._btnIcon = tool_btn(IconRegistry.from_name('mdi.emoticon-outline'), 'Change icon', transparent_=True)
        self._btnIcon.clicked.connect(self._showIconSelector)
        self._sbFont = FontSizeSpinBox()
        self._sbFont.fontChanged.connect(self._fontChanged)
        self._btnBold = tool_btn(IconRegistry.from_name('fa5s.bold'), 'Bold', checkable=True, icon_resize=False,
                                 properties=['transparent-rounded-bg-on-hover', 'top-selector'])
        self._btnItalic = tool_btn(IconRegistry.from_name('fa5s.italic'), 'Italic',
                                   checkable=True, icon_resize=False,
                                   properties=['transparent-rounded-bg-on-hover', 'top-selector'])
        self._btnUnderline = tool_btn(IconRegistry.from_name('fa5s.underline'), 'Underline',
                                      checkable=True, icon_resize=False,
                                      properties=['transparent-rounded-bg-on-hover', 'top-selector'])
        self._btnBold.clicked.connect(self._textStyleChanged)
        self._btnItalic.clicked.connect(self._textStyleChanged)
        self._btnUnderline.clicked.connect(self._textStyleChanged)

        self._eventSelector = EventSelectorWidget(self)
        self.addSecondaryWidget(self._btnType, self._eventSelector)
        self._eventSelector.selected.connect(self._typeChanged)

        self._toolbar.layout().addWidget(self._btnType)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._btnIcon)
        self._toolbar.layout().addWidget(self._btnColor)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._sbFont)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._btnBold)
        self._toolbar.layout().addWidget(self._btnItalic)
        self._toolbar.layout().addWidget(self._btnUnderline)

    def setItem(self, item: EventItem):
        self._item = item
        self._hideSecondarySelectors()

    def _fontChanged(self, size: int):
        self._hideSecondarySelectors()
        if self._item:
            self._item.setFontSettings(size=size)

    def _textStyleChanged(self):
        self._hideSecondarySelectors()
        if self._item:
            self._item.setFontSettings(bold=self._btnBold.isChecked(), italic=self._btnItalic.isChecked(),
                                       underline=self._btnUnderline.isChecked())

    def _typeChanged(self, itemType: ItemType):
        if self._item:
            self._item.setItemType(itemType)

    def _showIconSelector(self):
        result = IconSelectorDialog().display()
        if result and self._item:
            self._item.setIcon(IconRegistry.from_name(result[0], result[1].name()))
