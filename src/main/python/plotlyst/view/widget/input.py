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
from functools import partial

import fbs_runtime.platform
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer, QPoint
from PyQt5.QtGui import QKeySequence, QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QTextFormat, \
    QKeyEvent, QPaintEvent, QTextListFormat
from PyQt5.QtWidgets import QTextEdit, QFrame, QPushButton, QStylePainter, QStyleOptionButton, QStyle, QToolBar, \
    QAction, QActionGroup, QComboBox, QMenu
from overrides import overrides

from src.main.python.plotlyst.view.common import line
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

        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet('.QToolBar {background-color: rgb(255, 255, 255);}')
        self.setMargins(3, 3, 3, 3)
        self.toolbar.layout().setSpacing(5)
        self.layout().insertWidget(0, self.toolbar)
        self.textTitle = AutoAdjustableTextEdit()
        self.textTitle.setStyleSheet('border: 0px;')
        self.layout().insertWidget(1, self.textTitle)

        if fbs_runtime.platform.is_linux():
            self.textEditor.setFontFamily('Noto Sans Mono')
        elif fbs_runtime.platform.is_mac():
            self.textEditor.setFontFamily('Palatino')
        self.textEditor.cursorPositionChanged.connect(self._updateFormat)
        self.textEditor.setViewportMargins(5, 5, 5, 5)
        self.textEditor.setStyleSheet('QTextEdit {background: white; border: 0px;}')
        self.textEditor.installEventFilter(self)
        self.textEditor.setTabStopDistance(
            QtGui.QFontMetricsF(self.textEditor.font()).horizontalAdvance(' ') * 4)

        self.cbHeading = QComboBox()
        self.cbHeading.setStyleSheet('''
        QComboBox {
            border: 0px;
            padding: 1px 1px 1px 3px;
        }
        ''')

        self.cbHeading.addItem('Normal')
        self.cbHeading.addItem(IconRegistry.heading_1_icon(), '')
        self.cbHeading.addItem(IconRegistry.heading_2_icon(), '')
        self.cbHeading.addItem(IconRegistry.heading_3_icon(), '')
        self.cbHeading.setCurrentText('Normal')
        self.cbHeading.currentIndexChanged.connect(self._setHeading)

        self.actionBold = QAction(IconRegistry.from_name('fa5s.bold'), '')
        self.actionBold.triggered.connect(lambda x: self.textEditor.setFontWeight(QFont.Bold if x else QFont.Normal))
        self.actionBold.setCheckable(True)
        self.actionBold.setShortcut(QKeySequence.Bold)

        self.actionItalic = QAction(IconRegistry.from_name('fa5s.italic'), '')
        self.actionItalic.triggered.connect(self.textEditor.setFontItalic)
        self.actionItalic.setCheckable(True)
        self.actionItalic.setShortcut(QKeySequence.Italic)

        self.actionUnderline = QAction(IconRegistry.from_name('fa5s.underline'), '')
        self.actionUnderline.triggered.connect(self.textEditor.setFontUnderline)
        self.actionUnderline.setCheckable(True)
        self.actionUnderline.setShortcut(QKeySequence.Underline)

        self.actionAlignLeft = QAction(IconRegistry.from_name('fa5s.align-left'), '')
        self.actionAlignLeft.triggered.connect(lambda: self.textEditor.setAlignment(Qt.AlignLeft))
        self.actionAlignLeft.setCheckable(True)
        self.actionAlignLeft.setChecked(True)
        self.actionAlignLeft.setShortcut(QKeySequence.Underline)
        self.actionAlignCenter = QAction(IconRegistry.from_name('fa5s.align-center'), '')
        self.actionAlignCenter.triggered.connect(lambda: self.textEditor.setAlignment(Qt.AlignCenter))
        self.actionAlignCenter.setCheckable(True)
        self.actionAlignCenter.setShortcut(QKeySequence.Underline)
        self.actionAlignRight = QAction(IconRegistry.from_name('fa5s.align-right'), '')
        self.actionAlignRight.triggered.connect(lambda: self.textEditor.setAlignment(Qt.AlignRight))
        self.actionAlignRight.setCheckable(True)
        self.actionAlignRight.setShortcut(QKeySequence.Underline)

        self.actionInsertList = QAction(IconRegistry.from_name('fa5s.list'), '')
        self.actionInsertList.triggered.connect(
            lambda: self.textEditor.textCursor().insertList(QTextListFormat.ListDisc))
        self.actionInsertNumberedList = QAction(IconRegistry.from_name('fa5s.list-ol'), '')
        self.actionInsertNumberedList.triggered.connect(
            lambda: self.textEditor.textCursor().insertList(QTextListFormat.ListDecimal))

        self.actionGroupAlignment = QActionGroup(self.toolbar)
        self.actionGroupAlignment.addAction(self.actionAlignLeft)
        self.actionGroupAlignment.addAction(self.actionAlignCenter)
        self.actionGroupAlignment.addAction(self.actionAlignRight)

        self.toolbar.addWidget(self.cbHeading)
        self.toolbar.addAction(self.actionBold)
        self.toolbar.addAction(self.actionItalic)
        self.toolbar.addAction(self.actionUnderline)
        self.toolbar.addWidget(line(vertical=True))
        self.toolbar.addAction(self.actionAlignLeft)
        self.toolbar.addAction(self.actionAlignCenter)
        self.toolbar.addAction(self.actionAlignRight)
        self.toolbar.addWidget(line(vertical=True))
        self.toolbar.addAction(self.actionInsertList)
        self.toolbar.addAction(self.actionInsertNumberedList)

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

    def setToolbarVisible(self, visible: bool):
        self.toolbar.setVisible(visible)

    def setMargins(self, left: int, top: int, right: int, bottom: int):
        self.textEditor.setViewportMargins(left, top, right, bottom)

    def setFormat(self, lineSpacing: int = 100, textIndent: int = 20):
        blockFmt = QTextBlockFormat()
        blockFmt.setTextIndent(textIndent)
        blockFmt.setLineHeight(lineSpacing, QTextBlockFormat.ProportionalHeight)

        theCursor = self.textEditor.textCursor()
        theCursor.clearSelection()
        theCursor.select(QTextCursor.Document)
        theCursor.mergeBlockFormat(blockFmt)

    def clear(self):
        self.textEditor.clear()
        self.textTitle.clear()

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
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Slash:
                self._showCommands()

        return super(RichTextEditor, self).eventFilter(watched, event)

    def _updateFormat(self):
        self.actionBold.setChecked(self.textEditor.fontWeight() == QFont.Bold)
        self.actionItalic.setChecked(self.textEditor.fontItalic())
        self.actionUnderline.setChecked(self.textEditor.fontUnderline())

        self.actionAlignLeft.setChecked(self.textEditor.alignment() == Qt.AlignLeft)
        self.actionAlignCenter.setChecked(self.textEditor.alignment() == Qt.AlignCenter)
        self.actionAlignRight.setChecked(self.textEditor.alignment() == Qt.AlignRight)

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

    def _showCommands(self):
        def trigger(func):
            self.textEditor.textCursor().deletePreviousChar()
            func()

        rect = self.textEditor.cursorRect(self.textEditor.textCursor())

        menu = QMenu(self.textEditor)
        menu.addAction(IconRegistry.heading_1_icon(), '', partial(trigger, lambda: self.cbHeading.setCurrentIndex(1)))
        menu.addAction(IconRegistry.heading_2_icon(), '', partial(trigger, lambda: self.cbHeading.setCurrentIndex(2)))

        menu.popup(self.textEditor.viewport().mapToGlobal(QPoint(rect.x(), rect.y())))


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
