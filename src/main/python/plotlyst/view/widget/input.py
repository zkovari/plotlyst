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
from enum import Enum

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer
from PyQt5.QtGui import QKeySequence, QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QTextFormat, \
    QKeyEvent, QPaintEvent
from PyQt5.QtWidgets import QTextEdit, QFrame, QPushButton, QStylePainter, QStyleOptionButton, QStyle
from overrides import overrides

from src.main.python.plotlyst.view.generated.rich_text_editor_widget_ui import Ui_RichTextEditor
from src.main.python.plotlyst.view.icons import IconRegistry


class AutoAdjustableTextEdit(QTextEdit):
    def __init__(self, parent=None, height: int = 40):
        super(AutoAdjustableTextEdit, self).__init__(parent)
        self.textChanged.connect(self._resizeToContent)
        self._minHeight = height
        self.setMaximumHeight(self._minHeight)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    @overrides
    def setText(self, text: str) -> None:
        self.setPlainText(text)

    @overrides
    def setPlainText(self, text: str) -> None:
        super(AutoAdjustableTextEdit, self).setPlainText(text)
        QTimer.singleShot(50, self._resizeToContent)

    def _resizeToContent(self):
        size = self.document().size()
        self.setMaximumHeight(max(self._minHeight, size.height()))


class RichTextEditor(QFrame, Ui_RichTextEditor):
    def __init__(self, parent=None):
        super(RichTextEditor, self).__init__(parent)
        self.setupUi(self)

        self.textTitle = AutoAdjustableTextEdit()
        self.textTitle.setStyleSheet('border: 0px;')
        self.layout().insertWidget(1, self.textTitle)

        self.textEditor.cursorPositionChanged.connect(self._updateFormat)
        self.textEditor.installEventFilter(self)
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

    def setText(self, content: str, title: str = '', title_read_only: bool = False):
        self.textEditor.setHtml(content)
        self.textEditor.setFocus()
        self.textTitle.setHtml(f'''
                            <style>
                                h1 {{text-align: center;}}
                                </style>
                            <h1>{title}</h1>''')
        self.textTitle.setReadOnly(title_read_only)

    def setTitleVisible(self, visible: bool):
        self.textTitle.setVisible(visible)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(event, QKeyEvent):
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
                cursor = self.textEditor.textCursor()
                _list = cursor.block().textList()
                if _list and _list.count() > 1:
                    cursor.beginEditBlock()
                    block = cursor.block()
                    _list.remove(block)
                    _list.format().setIndent(_list.format().indent() + 1)
                    cursor.insertList(_list.format())

                    cursor.endEditBlock()
                    return True
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
                cursor = self.textEditor.textCursor()
                level = cursor.blockFormat().headingLevel()
                if level > 0:  # heading
                    cursor.insertBlock()
                    self.cbHeading.setCurrentIndex(0)
                    self._setHeading()
                    return True

        return super(RichTextEditor, self).eventFilter(watched, event)

    def _updateFormat(self):
        self.btnBold.setChecked(self.textEditor.fontWeight() == QFont.Bold)
        self.btnItalic.setChecked(self.textEditor.fontItalic())
        self.btnUnderline.setChecked(self.textEditor.fontUnderline())

        self.btnAlignLeft.setChecked(self.textEditor.alignment() == Qt.AlignLeft)
        self.btnAlignCenter.setChecked(self.textEditor.alignment() == Qt.AlignCenter)
        self.btnAlignRight.setChecked(self.textEditor.alignment() == Qt.AlignRight)

        self.cbHeading.blockSignals(True)
        cursor = self.textEditor.textCursor()
        level = cursor.blockFormat().headingLevel()
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


class RotatedButtonOrientation(Enum):
    VerticalTopToBottom = 0
    VerticalBottomToTop = 1


class RotatedButton(QPushButton):
    def __init__(self, parent=None):
        super(RotatedButton, self).__init__(parent)
        self._orientation = RotatedButtonOrientation.VerticalTopToBottom

    def setOrientation(self, orientation: RotatedButtonOrientation):
        self._orientation = orientation
        self.update()

    @overrides
    def paintEvent(self, event: QPaintEvent):
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        if self._orientation == RotatedButtonOrientation.VerticalTopToBottom:
            painter.rotate(90)
            painter.translate(0, -1 * self.width())
        else:
            painter.rotate(-90)
            painter.translate(-1 * self.height(), 0)
        option.rect = option.rect.transposed()
        painter.drawControl(QStyle.CE_PushButton, option)

    def sizeHint(self):
        size = super(RotatedButton, self).sizeHint()
        size.transpose()
        return size
