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
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QTextFormat
from PyQt5.QtWidgets import QTextEdit, QFrame

from src.main.python.plotlyst.view.generated.rich_text_editor_widget_ui import Ui_RichTextEditor
from src.main.python.plotlyst.view.icons import IconRegistry


class AutoAdjustableTextEdit(QTextEdit):
    def __init__(self, parent=None, height: int = 40):
        super(AutoAdjustableTextEdit, self).__init__(parent)
        self.textChanged.connect(self._resizeToContent)
        self._minHeight = height
        self.setMaximumHeight(self._minHeight)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def _resizeToContent(self):
        size = self.document().size()
        self.setMaximumHeight(max(self._minHeight, size.height()))


class RichTextEditor(QFrame, Ui_RichTextEditor):
    def __init__(self, parent=None):
        super(RichTextEditor, self).__init__(parent)
        self.setupUi(self)

        self.textEditor.cursorPositionChanged.connect(self._updateFormat)
        self.textEditor.setTabStopDistance(
            QtGui.QFontMetricsF(self.textEditor.font()).horizontalAdvance(' ') * 4)

        self.cbHeading.addItem('Normal')
        self.cbHeading.addItem(IconRegistry.from_name('mdi.format-header-1', mdi_scale=1.4), '')
        self.cbHeading.addItem(IconRegistry.from_name('mdi.format-header-2'), '')
        self.cbHeading.addItem(IconRegistry.from_name('mdi.format-header-3', mdi_scale=1), '')
        self.cbHeading.setCurrentText('Normal')
        self.cbHeading.currentIndexChanged.connect(self._setHeading)

        self.btnBold.setIcon(IconRegistry.from_name('fa5s.bold'))
        self.btnBold.setShortcut(QKeySequence.Bold)
        self.btnBold.clicked.connect(lambda x: self.textEditor.setFontWeight(QFont.Bold if x else QFont.Normal))

        self.btnItalic.setIcon(IconRegistry.from_name('fa5s.italic'))
        self.btnItalic.setShortcut(QKeySequence.Italic)
        self.btnItalic.clicked.connect(self.textEditor.setFontItalic)

        self.btnUnderline.setIcon(IconRegistry.from_name('fa5s.underline'))
        self.btnUnderline.setShortcut(QKeySequence.Underline)
        self.btnUnderline.clicked.connect(self.textEditor.setFontUnderline)

        self.btnAlignLeft.setIcon(IconRegistry.from_name('fa5s.align-left'))
        self.btnAlignLeft.clicked.connect(lambda: self.textEditor.setAlignment(Qt.AlignLeft))

        self.btnAlignCenter.setIcon(IconRegistry.from_name('fa5s.align-center'))
        self.btnAlignCenter.clicked.connect(lambda: self.textEditor.setAlignment(Qt.AlignCenter))

        self.btnAlignRight.setIcon(IconRegistry.from_name('fa5s.align-right'))
        self.btnAlignRight.clicked.connect(lambda: self.textEditor.setAlignment(Qt.AlignRight))

    def _updateFormat(self):
        self.btnBold.setChecked(self.textEditor.fontWeight() == QFont.Bold)
        self.btnItalic.setChecked(self.textEditor.fontItalic())
        self.btnUnderline.setChecked(self.textEditor.fontUnderline())

        self.btnAlignLeft.setChecked(self.textEditor.alignment() == Qt.AlignLeft)
        self.btnAlignCenter.setChecked(self.textEditor.alignment() == Qt.AlignCenter)
        self.btnAlignRight.setChecked(self.textEditor.alignment() == Qt.AlignRight)

        self.cbHeading.blockSignals(True)
        level = self.textEditor.textCursor().blockFormat().headingLevel()
        self.cbHeading.setCurrentIndex(level)
        self.cbHeading.blockSignals(False)

    def _setHeading(self):
        cursor: QTextCursor = self.textEditor.textCursor()
        cursor.beginEditBlock()

        blockFormat: QTextBlockFormat = cursor.blockFormat()
        blockFormat.setObjectIndex(-1)
        headingLevel = self.cbHeading.currentIndex()
        blockFormat.setHeadingLevel(headingLevel)
        cursor.setBlockFormat(blockFormat)
        sizeAdjustment = 5 - headingLevel if headingLevel else 0

        charFormat = QTextCharFormat()
        charFormat.setFontWeight(QFont.Bold if headingLevel else QFont.Normal)
        charFormat.setProperty(QTextFormat.FontSizeAdjustment, sizeAdjustment)
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.mergeCharFormat(charFormat)
        self.textEditor.mergeCurrentCharFormat(charFormat)

        cursor.endEditBlock()
