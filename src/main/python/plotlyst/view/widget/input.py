"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from typing import Optional

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer, QPoint, QSize, QMimeData
from PyQt5.QtGui import QKeySequence, QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QTextFormat, \
    QKeyEvent, QPaintEvent, QTextListFormat, QPainter, QBrush, QLinearGradient, QColor, QSyntaxHighlighter, \
    QTextDocument, QTextBlockUserData
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QTextEdit, QFrame, QPushButton, QStylePainter, QStyleOptionButton, QStyle, QToolBar, \
    QAction, QActionGroup, QComboBox, QMenu, QVBoxLayout, QApplication, QToolButton, QHBoxLayout, QLabel, QFileDialog, \
    QLineEdit
from fbs_runtime import platform
from language_tool_python import LanguageTool
from overrides import overrides
from slugify import slugify

from src.main.python.plotlyst.core.domain import TextStatistics
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import LanguageToolSet
from src.main.python.plotlyst.view.common import line, spacer_widget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget._toggle import AnimatedToggle
from src.main.python.plotlyst.view.widget.lang import GrammarPopupMenu
from src.main.python.plotlyst.worker.grammar import language_tool_proxy, dictionary


class AutoAdjustableTextEdit(QTextEdit):
    def __init__(self, parent=None, height: int = 25):
        super(AutoAdjustableTextEdit, self).__init__(parent)
        self.textChanged.connect(self._resizeToContent)
        self._minHeight = height
        self.setAcceptRichText(False)
        self.setFixedHeight(self._minHeight)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    @overrides
    def setText(self, text: str) -> None:
        self.setPlainText(text)

    @overrides
    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        self._resizeToContent()

    def _resizeToContent(self):
        size = self.document().size()
        self.setFixedHeight(max(self._minHeight, size.height()))


class TextBlockData(QTextBlockUserData):
    def __init__(self):
        super(TextBlockData, self).__init__()
        self._misspellings = []
        self._wordCount: int = -1

    @property
    def misspellings(self):
        return self._misspellings

    @misspellings.setter
    def misspellings(self, value):
        self._misspellings.clear()
        self._misspellings.extend(value)

    @property
    def wordCount(self):
        return self._wordCount

    @wordCount.setter
    def wordCount(self, value):
        self._wordCount = value


class AbstractTextBlockHighlighter(QSyntaxHighlighter):
    def _currentblockData(self) -> TextBlockData:
        data = self.currentBlockUserData()
        if data is None or not isinstance(data, TextBlockData):
            data = TextBlockData()
            self.setCurrentBlockUserData(data)

        return data


# partially based on https://gist.github.com/ssokolow/0e69b9bd9ca442163164c8a9756aa15f
class GrammarHighlighter(AbstractTextBlockHighlighter, EventListener):

    def __init__(self, document: QTextDocument, checkEnabled: bool = True):
        super(GrammarHighlighter, self).__init__(document)
        self._checkEnabled: bool = checkEnabled

        self._misspelling_format = QTextCharFormat()
        self._misspelling_format.setUnderlineColor(QColor('#d90429'))
        self._misspelling_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)

        self._style_format = QTextCharFormat()
        self._style_format.setUnderlineColor(QColor('#5e60ce'))
        self._style_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)

        self._grammar_format = QTextCharFormat()
        self._grammar_format.setUnderlineColor(QColor('#ffc300'))
        self._grammar_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)

        self._formats_per_issue = {'misspelling': self._misspelling_format, 'style': self._style_format}

        self._language_tool: Optional[LanguageTool] = None
        if language_tool_proxy.is_set():
            self._language_tool = language_tool_proxy.tool

        self._currentAsyncBlock: int = 0
        self._asyncTimer = QTimer()
        self._asyncTimer.setInterval(20)
        self._asyncTimer.timeout.connect(self._highlightNextBlock)

        event_dispatcher.register(self, LanguageToolSet)

    def checkEnabled(self) -> bool:
        return self._checkEnabled

    def setCheckEnabled(self, enabled: bool):
        self._checkEnabled = enabled
        if not enabled:
            self._asyncTimer.stop()

    @overrides
    def setDocument(self, doc: Optional[QTextDocument]) -> None:
        self._asyncTimer.stop()
        super(GrammarHighlighter, self).setDocument(doc)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, LanguageToolSet):
            self._language_tool = language_tool_proxy.tool
            self.asyncRehighlight()

    @overrides
    def highlightBlock(self, text: str) -> None:
        if self._checkEnabled and self._language_tool:
            matches = self._language_tool.check(text)
            misspellings = []
            for m in matches:
                if dictionary.is_known_word(text[m.offset:m.offset + m.errorLength]):
                    continue
                self.setFormat(m.offset, m.errorLength,
                               self._formats_per_issue.get(m.ruleIssueType, self._grammar_format))
                misspellings.append((m.offset, m.errorLength, m.replacements, m.message, m.ruleIssueType))
            data = self._currentblockData()
            data.misspellings = misspellings

    def asyncRehighlight(self):
        if self._checkEnabled and self._language_tool:
            self._currentAsyncBlock = 0
            self._asyncTimer.start()

    def _highlightNextBlock(self):
        if self._currentAsyncBlock >= self.document().blockCount():
            return self._asyncTimer.stop()

        block = self.document().findBlockByNumber(self._currentAsyncBlock)
        self.rehighlightBlock(block)
        self._currentAsyncBlock += 1


class BlockStatistics(AbstractTextBlockHighlighter):

    @overrides
    def highlightBlock(self, text: str) -> None:
        data = self._currentblockData()
        wc = len([x for x in text.split(' ') if x])
        data.wordCount = wc


class _TextEditor(QTextEdit):

    def __init__(self, parent=None):
        super(_TextEditor, self).__init__(parent)
        self._pasteAsPlain: bool = False
        self._blockStatistics = BlockStatistics(self.document())

    def setPasteAsPlainText(self, plain: bool):
        self._pasteAsPlain = plain

    def statistics(self) -> TextStatistics:
        wc = 0
        for i in range(self.document().blockCount()):
            block = self.document().findBlockByNumber(i)
            data = block.userData()
            if isinstance(data, TextBlockData):
                wc += data.wordCount

        return TextStatistics(wc)

    @overrides
    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super(_TextEditor, self).mouseMoveEvent(event)
        cursor = self.cursorForPosition(event.pos())
        if cursor.atBlockStart() or cursor.atBlockEnd():
            QApplication.restoreOverrideCursor()
            return

        for start, length, replacements, msg, style in self._errors(cursor):
            if start <= cursor.positionInBlock() <= start + length:
                if QApplication.overrideCursor() is None:
                    QApplication.setOverrideCursor(Qt.PointingHandCursor)
                return
        QApplication.restoreOverrideCursor()

    @overrides
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        super(_TextEditor, self).mousePressEvent(event)
        QApplication.restoreOverrideCursor()
        cursor = self.cursorForPosition(event.pos())
        if cursor.atBlockStart() or cursor.atBlockEnd():
            QApplication.restoreOverrideCursor()
            return

        for start, length, replacements, msg, style in self._errors(cursor):
            if start <= cursor.positionInBlock() <= start + length:
                menu = GrammarPopupMenu(self)
                menu.init(replacements, msg, style)
                pos = self.mapToGlobal(event.pos())
                pos.setY(pos.y() + self.viewportMargins().top())
                pos.setX(pos.x() + self.viewportMargins().left())
                menu.popupWidget().replacementRequested.connect(partial(self._replaceWord, cursor, start, length))
                menu.popup(pos)

    @overrides
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        cursor = self.textCursor()
        if event.key() == Qt.Key_Tab:
            list_ = cursor.block().textList()
            if list_:
                cursor.beginEditBlock()
                block = cursor.block()

                new_format = list_.format()
                new_format.setIndent(list_.format().indent() + 1)
                cursor.insertList(new_format)
                list_.removeItem(list_.itemNumber(block))
                cursor.deletePreviousChar()

                cursor.endEditBlock()
                return
        if event.key() == Qt.Key_Backtab:
            list_ = cursor.block().textList()
            if list_:
                indent = list_.format().indent()
                if indent > 1:
                    cursor.beginEditBlock()
                    new_format = list_.format()
                    new_format.setIndent(indent - 1)
                    list_.setFormat(new_format)
                    cursor.endEditBlock()
                return
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
            level = cursor.blockFormat().headingLevel()
            if level > 0:  # heading
                cursor.insertBlock()
                self.cbHeading.setCurrentIndex(0)
                self._setHeading()
                return
        super(_TextEditor, self).keyPressEvent(event)

    @overrides
    def insertFromMimeData(self, source: QMimeData) -> None:
        if self._pasteAsPlain:
            self.insertPlainText(source.text())
        else:
            super(_TextEditor, self).insertFromMimeData(source)

    def _errors(self, cursor: QTextCursor):
        data = cursor.block().userData()
        if data and isinstance(data, TextBlockData):
            return data.misspellings

        return []

    # def paintEvent(self, event: QtGui.QPaintEvent) -> None:
    #     super(_TextEditor, self).paintEvent(event)
    #     painter = QPainter(self.viewport())
    #     painter.setRenderHint(QPainter.Antialiasing)
    #     painter.setPen(QPen(QColor('#02bcd4'), 20, Qt.SolidLine))
    #     painter.setBrush(QColor('#02bcd4'))
    #     # painter.begin()
    #     # painter.setPen(QPen(Qt.black), 12, Qt.SolidLine)
    #     self.textCursor().position()
    #     rect = self.cursorRect(self.textCursor())
    #     painter.drawText(rect.x(), rect.y(), 'Painted text')
    #     # painter.drawLine(0, 0, self.width(), self.height())

    def _replaceWord(self, cursor: QTextCursor, start: int, length: int, replacement: str):
        block_pos = cursor.block().position()
        cursor.setPosition(block_pos + start, QTextCursor.MoveAnchor)
        cursor.setPosition(block_pos + start + length, QTextCursor.KeepAnchor)
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(replacement)
        cursor.endEditBlock()
        QApplication.restoreOverrideCursor()


class CapitalizationEventFilter(QObject):

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(event, QKeyEvent) and event.type() == QEvent.KeyPress:
            if event.text().isalpha() and self._empty(watched) and 'filter' not in watched.objectName().lower():
                inserted = self._insert(watched, event.text().upper())
                if inserted:
                    return True
        return super(CapitalizationEventFilter, self).eventFilter(watched, event)

    def _empty(self, widget) -> bool:
        if isinstance(widget, QLineEdit):
            return not widget.text()
        elif isinstance(widget, QTextEdit):
            return not widget.toPlainText()
        return False

    def _insert(self, widget, text: str) -> bool:
        if isinstance(widget, QLineEdit):
            widget.insert(text)
            return True
        elif isinstance(widget, QTextEdit):
            widget.insertPlainText(text)
            return True
        return False


class RichTextEditor(QFrame):
    def __init__(self, parent=None):
        super(RichTextEditor, self).__init__(parent)

        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(2, 2, 2, 2)

        self.toolbar = QToolBar()
        if platform.is_mac():
            self.toolbar.setIconSize(QSize(15, 15))
        else:
            self.toolbar.setIconSize(QSize(17, 17))
        self.toolbar.setStyleSheet('.QToolBar {background-color: rgb(255, 255, 255);}')
        self.toolbar.layout().setSpacing(5)
        self.textTitle = AutoAdjustableTextEdit(height=50)
        self.textTitle.setStyleSheet('border: 0px;')

        self.textEditor = _TextEditor()
        self.textEditor.setMouseTracking(True)
        self.textEditor.setAutoFormatting(QTextEdit.AutoAll)

        self.textEditor.cursorPositionChanged.connect(self._updateFormat)
        self.textEditor.setViewportMargins(5, 5, 5, 5)

        if platform.is_linux():
            family = 'Noto Sans Mono'
        elif platform.is_mac():
            family = 'Helvetica Neue'
        else:
            family = 'Helvetica'
        self.textEditor.setStyleSheet(f'QTextEdit {{background: white; border: 0px; font: {family}}}')
        self.textEditor.setFontFamily(family)

        self._lblPlaceholder = QLabel(self.textEditor)
        font = QFont(family)
        font.setItalic(True)
        self._lblPlaceholder.setFont(font)
        self._lblPlaceholder.setStyleSheet('color: #118ab2;')

        self.setFontPointSize(16)

        self.setMouseTracking(True)
        self.textEditor.installEventFilter(self)
        self.textEditor.setMouseTracking(True)
        self.textEditor.setTabStopDistance(
            QtGui.QFontMetricsF(self.textEditor.font()).horizontalAdvance(' ') * 4)
        self.setMargins(3, 3, 3, 3)

        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.textTitle)
        self.layout().addWidget(self.textEditor)

        self.cbHeading = QComboBox()
        if platform.is_linux() or platform.is_windows():
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

        self.actionExportToPdf = QAction(IconRegistry.from_name('mdi.file-export-outline'), '')
        self.actionExportToPdf.triggered.connect(self._exportPdf)

        self.actionPrint = QAction(IconRegistry.from_name('mdi.printer'), '')
        self.actionPrint.triggered.connect(self._print)

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
        self.toolbar.addWidget(spacer_widget())
        self.toolbar.addAction(self.actionExportToPdf)
        self.toolbar.addAction(self.actionPrint)

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

    def setPasteAsPlainText(self, plain: bool):
        self.textEditor.setPasteAsPlainText(plain)

    def setMargins(self, left: int, top: int, right: int, bottom: int):
        self.textEditor.setViewportMargins(left, top, right, bottom)

    def setFormat(self, lineSpacing: int = 100, textIndent: int = 20):
        blockFmt = QTextBlockFormat()
        blockFmt.setTextIndent(textIndent)
        blockFmt.setLineHeight(lineSpacing, QTextBlockFormat.ProportionalHeight)

        cursor = self.textEditor.textCursor()
        cursor.clearSelection()
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(blockFmt)

    def setFontPointSize(self, size: int):
        self.textEditor.textCursor().select(QTextCursor.Document)
        self.textEditor.setFontPointSize(size)
        font = self._lblPlaceholder.font()
        font.setPointSize(size)
        self._lblPlaceholder.setFont(font)
        self.textEditor.textCursor().clearSelection()

    def clear(self):
        self.textEditor.clear()
        self.textTitle.clear()

    def statistics(self) -> TextStatistics:
        return self.textEditor.statistics()

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(event, QKeyEvent):
            # if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
            #     if self._lblPlaceholder.isVisible():
            #         self.textEditor.textCursor().insertText(self._lblPlaceholder.text())
            #         self._lblPlaceholder.hide()
            #         return True
            # elif event.type() == QEvent.KeyPress and self._lblPlaceholder.isVisible():
            #     self._lblPlaceholder.hide()
            if self.toolbar.isHidden() and event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_I and event.modifiers() & Qt.ControlModifier:
                    self.textEditor.setFontItalic(not self.textEditor.fontItalic())
                if event.key() == Qt.Key_B and event.modifiers() & Qt.ControlModifier:
                    self.textEditor.setFontWeight(
                        QFont.Bold if self.textEditor.fontWeight() == QFont.Normal else QFont.Normal)

            cursor = self.textEditor.textCursor()
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Slash:
                if self.textEditor.textCursor().atBlockStart():
                    self._showCommands()

            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Space:
                cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
                if cursor.selectedText() == ' ':
                    self.textEditor.textCursor().deletePreviousChar()
                    self.textEditor.textCursor().insertText('.')
            elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_QuoteDbl:
                self.textEditor.textCursor().insertText(event.text())
                cursor.movePosition(QTextCursor.PreviousCharacter)
                self.textEditor.setTextCursor(cursor)
            # elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            #     self._lblPlaceholder.setText(' said ')
            #     self._lblPlaceholder.show()
            #     rect = self.textEditor.cursorRect(cursor)
            #     self._lblPlaceholder.move(rect.x() + self.textEditor.viewportMargins().left(),
            #                               rect.y() + self.textEditor.viewportMargins().top())

        return super(RichTextEditor, self).eventFilter(watched, event)

    def _atSentenceStart(self, cursor: QTextCursor) -> bool:
        if cursor.atBlockStart():
            return True

        cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
        if cursor.selectedText() == '.':
            return True
        if cursor.atBlockStart() and cursor.selectedText() == '"':
            return True
        if cursor.positionInBlock() == 1:
            return False
        elif cursor.selectedText() == ' ' or cursor.selectedText() == '"':
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
            if cursor.selectedText().startswith('.'):
                return True

        return False

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

    def _exportPdf(self):
        title = slugify(self.textTitle.toPlainText(), separator='_')
        fn, _ = QFileDialog.getSaveFileName(self, 'Export PDF', f'{title}.pdf',
                                            'PDF files (*.pdf);;All Files()')
        if fn:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(fn)
            printer.setDocName(self.textTitle.toPlainText())
            self.__printHtml(printer)

    def _print(self):
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self.__printHtml(printer)

    def __printHtml(self, printer: QPrinter):
        richtext = RichTextEditor()  # create a new instance without the highlighters associated to it
        richtext.setText(self.textEditor.toHtml())
        richtext.textEditor.print(printer)


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

    @overrides
    def sizeHint(self):
        size = super(RotatedButton, self).sizeHint()
        size.transpose()
        return size


class Toggle(AnimatedToggle):
    def __init__(self, parent=None):
        super(Toggle, self).__init__(parent=parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(50)


class _PowerBar(QFrame):
    def __init__(self, steps: int = 10, startColor: str = 'red', endColor: str = 'green', parent=None):
        super(_PowerBar, self).__init__(parent)
        self.steps = steps
        self.startColor = startColor
        self.endColor = endColor
        self.value: int = 0

    @overrides
    def sizeHint(self) -> QSize:
        return QSize(10 * self.steps, 30)

    @overrides
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(self.startColor))
        gradient.setColorAt(1, QColor(self.endColor))
        brush = QBrush(gradient)
        painter.setBrush(brush)

        painter.fillRect(0, 0, self.value * 10, self.height(), brush)

        painter.end()

    def increase(self):
        if self.value < self.steps:
            self.value += 1
            self.update()

    def decrease(self):
        if self.value > 0:
            self.value -= 1
            self.update()


class PowerBar(QFrame):
    MINUS_COLOR_IDLE: str = '#c75146'
    MINUS_COLOR_ACTIVE: str = '#ad2e24'
    PLUS_COLOR_IDLE: str = '#52b788'
    PLUS_COLOR_ACTIVE: str = '#81171b'

    def __init__(self, parent=None):
        super(PowerBar, self).__init__(parent)

        self.setFrameStyle(QFrame.Box)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(3)
        self.btnMinus = QToolButton()
        self.btnMinus.setIcon(IconRegistry.minus_icon(self.MINUS_COLOR_IDLE))
        self.btnPlus = QToolButton()
        self.btnPlus.setIcon(IconRegistry.plus_circle_icon(self.PLUS_COLOR_IDLE))
        self._styleButton(self.btnMinus)
        self._styleButton(self.btnPlus)
        self.btnMinus.clicked.connect(self.decrease)
        self.btnPlus.clicked.connect(self.increase)

        self._bar = _PowerBar(startColor='#e1ecf7', endColor='#2ec4b6')
        self.layout().addWidget(self.btnMinus)
        self.layout().addWidget(self._bar)
        self.layout().addWidget(self.btnPlus)

    def _styleButton(self, button: QToolButton):
        button.setStyleSheet('border: 0px;')
        button.installEventFilter(self)
        button.setIconSize(QSize(14, 14))
        button.setCursor(Qt.PointingHandCursor)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QToolButton):
            if event.type() == QEvent.Enter:
                watched.setIconSize(QSize(16, 16))
            elif event.type() == QEvent.Leave:
                watched.setIconSize(QSize(14, 14))

        return super(PowerBar, self).eventFilter(watched, event)

    def value(self) -> int:
        return self._bar.value

    def decrease(self):
        self.btnMinus.setIcon(IconRegistry.minus_icon(self.MINUS_COLOR_ACTIVE))
        QTimer.singleShot(100, lambda: self.btnMinus.setIcon(IconRegistry.minus_icon(self.MINUS_COLOR_IDLE)))
        self._bar.decrease()

    def increase(self):
        self.btnPlus.setIcon(IconRegistry.plus_circle_icon(self.PLUS_COLOR_ACTIVE))
        QTimer.singleShot(100, lambda: self.btnPlus.setIcon(IconRegistry.plus_circle_icon(self.PLUS_COLOR_IDLE)))
        self._bar.increase()
