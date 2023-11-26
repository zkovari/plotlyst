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
import math
from enum import Enum
from functools import partial
from typing import Optional

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QObject, QEvent, QTimer, QPoint, QSize, pyqtSignal, QModelIndex, QItemSelectionModel
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QKeyEvent, QPaintEvent, QPainter, QBrush, QLinearGradient, \
    QColor, QSyntaxHighlighter, \
    QTextDocument, QTextBlockUserData, QIcon
from PyQt6.QtWidgets import QTextEdit, QFrame, QPushButton, QStylePainter, QStyleOptionButton, QStyle, QMenu, \
    QApplication, QToolButton, QLineEdit, QWidgetAction, QListView, QSpinBox, QWidget, QLabel
from language_tool_python import LanguageTool
from overrides import overrides
from qthandy import transparent, hbox, margins, pointy
from qttextedit import EnhancedTextEdit, RichTextEditor, DashInsertionMode, remove_font

from src.main.python.plotlyst.core.domain import TextStatistics, Character
from src.main.python.plotlyst.core.text import wc
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import global_event_dispatcher
from src.main.python.plotlyst.events import LanguageToolSet
from src.main.python.plotlyst.model.characters_model import CharactersTableModel
from src.main.python.plotlyst.model.common import proxy
from src.main.python.plotlyst.service.grammar import language_tool_proxy, dictionary
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import action
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.style.text import apply_texteditor_toolbar_style
from src.main.python.plotlyst.view.widget._toggle import AnimatedToggle
from src.main.python.plotlyst.view.widget.lang import GrammarPopupMenu


class AutoAdjustableTextEdit(EnhancedTextEdit):
    def __init__(self, parent=None, height: int = 25):
        super(AutoAdjustableTextEdit, self).__init__(parent)
        self.textChanged.connect(self._resizeToContent)
        self._minHeight = height
        self._resizedOnShow: bool = False
        self.setAcceptRichText(False)
        self.setFixedHeight(self._minHeight)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setDocumentMargin(0)
        self.setSidebarEnabled(False)

    @overrides
    def setText(self, text: str) -> None:
        self.setPlainText(text)

    @overrides
    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        if not self._resizedOnShow:
            self._resizeToContent()
            self._resizedOnShow = True

    def _resizeToContent(self):
        size = self.document().size()
        self.setFixedHeight(max(self._minHeight, math.ceil(size.height())))


class AutoAdjustableLineEdit(QLineEdit):
    def __init__(self, parent=None, defaultWidth: int = 200):
        super(AutoAdjustableLineEdit, self).__init__(parent)
        self._padding = 10
        self._defaultWidth = defaultWidth + self._padding
        self._resizedOnShow: bool = False
        self.setFixedWidth(self._defaultWidth)
        self.textChanged.connect(self._resizeToContent)

    @overrides
    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        if not self._resizedOnShow:
            self._resizeToContent()
            self._resizedOnShow = True

    def _resizeToContent(self):
        text = self.text().strip()
        if text:
            text_width = self.fontMetrics().boundingRect(text).width()
            width = max(text_width + self._padding, self._defaultWidth)
            self.setFixedWidth(width)
        else:
            self.setFixedWidth(self._defaultWidth)


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


class GrammarHighlightStyle(Enum):
    UNDERLINE = 1
    BACKGOUND = 2


# partially based on https://gist.github.com/ssokolow/0e69b9bd9ca442163164c8a9756aa15f
class GrammarHighlighter(AbstractTextBlockHighlighter, EventListener):

    def __init__(self, document: QTextDocument, checkEnabled: bool = True,
                 highlightStyle: GrammarHighlightStyle = GrammarHighlightStyle.UNDERLINE):
        super(GrammarHighlighter, self).__init__(document)
        self._checkEnabled: bool = checkEnabled

        self._misspelling_format = QTextCharFormat()
        self._misspelling_format.setUnderlineColor(QColor('#d90429'))
        if highlightStyle == GrammarHighlightStyle.BACKGOUND:
            self._misspelling_format.setBackground(QBrush(QColor('#fbe0dd')))
        self._misspelling_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)

        self._style_format = QTextCharFormat()
        self._style_format.setUnderlineColor(QColor('#5a189a'))
        if highlightStyle == GrammarHighlightStyle.BACKGOUND:
            self._style_format.setBackground(QBrush(QColor('#dec9e9')))
        self._style_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)

        self._grammar_format = QTextCharFormat()
        self._grammar_format.setUnderlineColor(QColor('#ffc300'))
        if highlightStyle == GrammarHighlightStyle.BACKGOUND:
            self._grammar_format.setBackground(QBrush(QColor('#fffae6')))
        self._grammar_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)

        self._formats_per_issue = {'misspelling': self._misspelling_format, 'style': self._style_format}

        self._language_tool: Optional[LanguageTool] = None
        if language_tool_proxy.is_set():
            self._language_tool = language_tool_proxy.tool

        self._currentAsyncBlock: int = 0
        self._asyncTimer = QTimer()
        self._asyncTimer.setInterval(20)
        self._asyncTimer.timeout.connect(self._highlightNextBlock)

        global_event_dispatcher.register(self, LanguageToolSet)

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
        data = self._currentblockData()
        if self._checkEnabled and self._language_tool:
            matches = self._language_tool.check(text)
            misspellings = []
            for m in matches:
                if dictionary.is_known_word(text[m.offset:m.offset + m.errorLength]):
                    continue
                self.setFormat(m.offset, m.errorLength,
                               self._formats_per_issue.get(m.ruleIssueType, self._grammar_format))
                misspellings.append((m.offset, m.errorLength, m.replacements, m.message, m.ruleIssueType))
            data.misspellings = misspellings
        else:
            data.misspellings.clear()

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
        data.wordCount = wc(text)


class CharacterContentAssistMenu(QMenu):
    characterSelected = pyqtSignal(Character)

    def __init__(self, parent=None):
        super(CharacterContentAssistMenu, self).__init__(parent)
        self.novel = app_env.novel
        self.lstCharacters = QListView(self)
        self.model = CharactersTableModel(self.novel)
        self._proxy = proxy(self.model)
        self.lstCharacters.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lstCharacters.clicked.connect(self._clicked)
        self.lstCharacters.setModel(self._proxy)

    def init(self, text: str = ''):
        action = QWidgetAction(self)

        action.setDefaultWidget(self.lstCharacters)
        self._proxy.setFilterRegularExpression(f'^{text}')
        if self._proxy.rowCount():
            self.lstCharacters.selectionModel().select(self._proxy.index(0, 0), QItemSelectionModel.Select)
        self.addAction(action)

    @overrides
    def popup(self, pos: QPoint) -> None:
        if self._proxy.rowCount() == 1:
            character = self._proxy.index(0, 0).data(CharactersTableModel.CharacterRole)
            self.characterSelected.emit(character)
        elif self._proxy.rowCount() > 1:
            super(CharacterContentAssistMenu, self).popup(pos)

    @overrides
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        super(CharacterContentAssistMenu, self).keyPressEvent(event)
        if event.key() == Qt.Key.Key_Return:
            indexes = self.lstCharacters.selectedIndexes()
            if indexes:
                self._clicked(indexes[0])

    def _clicked(self, index: QModelIndex):
        char = index.data(CharactersTableModel.CharacterRole)
        self.characterSelected.emit(char)


class TextEditBase(EnhancedTextEdit):

    def __init__(self, parent=None):
        super(TextEditBase, self).__init__(parent)
        self._blockStatistics = BlockStatistics(self.document())
        self.setDashInsertionMode(DashInsertionMode.INSERT_EM_DASH)
        self.setAutoCapitalizationEnabled(True)

    def statistics(self) -> TextStatistics:
        wc = 0
        for i in range(self.document().blockCount()):
            block = self.document().findBlockByNumber(i)
            data = block.userData()
            if isinstance(data, TextBlockData):
                wc += data.wordCount

        return TextStatistics(wc)

    @overrides
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        super(TextEditBase, self).keyPressEvent(event)
        if event.key() == Qt.Key.Key_Space and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            menu = CharacterContentAssistMenu(self)
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            menu.init(cursor.selectedText())
            menu.characterSelected.connect(self._insertCharacterName)
            menu.characterSelected.connect(menu.hide)
            rect = self.cursorRect(self.textCursor())
            self._popupMenu(menu, QPoint(rect.x(), rect.y()))

    @overrides
    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super(TextEditBase, self).mouseMoveEvent(event)
        cursor = self.cursorForPosition(event.pos())
        if cursor.atBlockStart() or cursor.atBlockEnd():
            QApplication.restoreOverrideCursor()
            return

        for start, length, replacements, msg, style in self._errors(cursor):
            if start <= cursor.positionInBlock() <= start + length:
                if QApplication.overrideCursor() is None:
                    QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
                return
        QApplication.restoreOverrideCursor()

    @overrides
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        super(TextEditBase, self).mousePressEvent(event)
        QApplication.restoreOverrideCursor()
        cursor = self.cursorForPosition(event.pos())
        if cursor.atBlockStart() or cursor.atBlockEnd():
            QApplication.restoreOverrideCursor()
            return

        for start, length, replacements, msg, style in self._errors(cursor):
            if start <= cursor.positionInBlock() <= start + length:
                menu = GrammarPopupMenu(self)
                menu.init(replacements, msg, style)
                menu.popupWidget().replacementRequested.connect(partial(self._replaceWord, cursor, start, length))
                self._popupMenu(menu, event.pos())

    def _popupMenu(self, menu: QMenu, pos: QPoint):
        global_pos = self.mapToGlobal(pos)
        global_pos.setY(global_pos.y() + self.viewportMargins().top())
        global_pos.setX(global_pos.x() + self.viewportMargins().left())
        menu.popup(global_pos)

    def _errors(self, cursor: QTextCursor):
        data = cursor.block().userData()
        if data and isinstance(data, TextBlockData):
            return data.misspellings

        return []

    # def paintEvent(self, event: QtGui.QPaintEvent) -> None:
    #     super(_TextEditor, self).paintEvent(event)
    #     painter = QPainter(self.viewport())
    #     painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    #     painter.setPen(QPen(QColor('#02bcd4'), 20, Qt.PenStyle.SolidLine))
    #     painter.setBrush(QColor('#02bcd4'))
    #     # painter.begin()
    #     # painter.setPen(QPen(Qt.GlobalColor.black), 12, Qt.PenStyle.SolidLine)
    #     self.textCursor().position()
    #     rect = self.cursorRect(self.textCursor())
    #     painter.drawText(rect.x(), rect.y(), 'Painted text')
    #     # painter.drawLine(0, 0, self.width(), self.height())

    def _replaceWord(self, cursor: QTextCursor, start: int, length: int, replacement: str):
        block_pos = cursor.block().position()
        cursor.setPosition(block_pos + start, QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(block_pos + start + length, QTextCursor.MoveMode.KeepAnchor)
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(replacement)
        cursor.endEditBlock()
        QApplication.restoreOverrideCursor()

    def _insertCharacterName(self, character: Character):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.removeSelectedText()
        cursor.insertText(character.name)
        cursor.endEditBlock()


class DocumentTextEdit(TextEditBase):
    grammarCheckToggled = pyqtSignal(bool)

    @overrides
    def createEnhancedContextMenu(self, pos: QPoint) -> QMenu:
        menu = super(DocumentTextEdit, self).createEnhancedContextMenu(pos)

        menu.addSeparator()
        grammar_action = action('Grammar check', slot=self.grammarCheckToggled.emit, parent=menu, checkable=True)
        grammar_action.setChecked(app_env.novel.prefs.docs.grammar_check)
        menu.addAction(grammar_action)
        return menu


class CapitalizationEventFilter(QObject):

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress:
            if event.text().isalpha() and (self._empty(watched) or self._selectedAll(
                    watched)) and 'filter' not in watched.objectName().lower() and not self._readOnly(watched):
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

    def _readOnly(self, widget) -> bool:
        if isinstance(widget, QLineEdit):
            return widget.isReadOnly()
        elif isinstance(widget, QTextEdit):
            return widget.isReadOnly()
        return False

    def _selectedAll(self, widget) -> bool:
        if isinstance(widget, QLineEdit):
            return widget.hasSelectedText() and widget.selectedText() == widget.text()
        elif isinstance(widget, QTextEdit):
            cursor = widget.textCursor()
            return cursor.hasSelection() and cursor.selectedText() == widget.toPlainText()
        return False

    def _insert(self, widget, text: str) -> bool:
        if isinstance(widget, QLineEdit):
            widget.insert(text)
            return True
        elif isinstance(widget, QTextEdit):
            widget.insertPlainText(text)
            return True
        return False


class DocumentTextEditor(RichTextEditor):
    titleChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(DocumentTextEditor, self).__init__(parent)
        self._titleVisible: bool = True

        self._btnIcon = QToolButton()
        transparent(self._btnIcon)
        self._btnIcon.setIconSize(QSize(40, 40))
        self._textTitle = QLineEdit()
        self._textTitle.setProperty('transparent', True)
        self._textTitle.setFrame(False)
        title_font = self._textTitle.font()
        title_font.setBold(True)
        title_font.setPointSize(40)
        self._textTitle.setFont(title_font)
        self._textTitle.returnPressed.connect(self.textEdit.setFocus)
        self._textTitle.textChanged.connect(self.titleChanged.emit)

        apply_texteditor_toolbar_style(self.toolbar())

        self._wdgTitle = group(self._btnIcon, self._textTitle, margin=0, spacing=0)
        self._wdgTitle.setProperty('relaxed-white-bg', True)
        margins(self._wdgTitle, top=20, bottom=5)
        self.setProperty('relaxed-white-bg', True)

        self.textEdit.setViewportMargins(5, 5, 5, 5)

        self.highlighter = self._initHighlighter()

        if app_env.is_mac():
            family = 'Helvetica Neue'
        elif app_env.is_windows():
            family = 'Calibri'
        else:
            family = 'Helvetica'
        self.textEdit.setFont(QFont(family, 16))
        self.textEdit.setProperty('transparent', True)
        self.textEdit.zoomIn(int(self.textEdit.font().pointSize() * 0.34))
        self.textEdit.setBlockFormat(lineSpacing=120)
        self.textEdit.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self.textEdit.setPlaceholderText('Write your notes...')

        self.setWidthPercentage(90)

        self.layout().insertWidget(1, self._wdgTitle)

        self._textedit.verticalScrollBar().valueChanged.connect(self._scrolled)

    @overrides
    def _initTextEdit(self) -> EnhancedTextEdit:
        def grammarCheckToggled(toggled: bool):
            app_env.novel.prefs.docs.grammar_check = toggled
            RepositoryPersistenceManager.instance().update_novel(app_env.novel)

            self.setGrammarCheckEnabled(toggled)
            if toggled:
                self.asyncCheckGrammer()
            else:
                self.checkGrammar()

        textedit = DocumentTextEdit(self)
        textedit.grammarCheckToggled.connect(grammarCheckToggled)
        return textedit

    @overrides
    def _resize(self):
        super(DocumentTextEditor, self)._resize()
        margins(self._wdgTitle, left=self.textEdit.viewportMargins().left())

    def _initHighlighter(self) -> GrammarHighlighter:
        return GrammarHighlighter(self.textEdit.document(), checkEnabled=False)

    def setText(self, content: str, title: str = '', icon: Optional[QIcon] = None, title_read_only: bool = False):
        self.textEdit.setHtml(remove_font(content))
        self.textEdit.setFocus()
        self._textTitle.setText(title)
        self._textTitle.setReadOnly(title_read_only)
        self.setTitleIcon(icon)
        self._textTitle.setVisible(self._titleVisible)

    def setTitleIcon(self, icon: Optional[QIcon] = None):
        self._btnIcon.setVisible(icon is not None)
        if icon:
            self._btnIcon.setIcon(icon)

    def setPlaceholderText(self, text: str):
        self.textEdit.setPlaceholderText(text)

    def setTitleVisible(self, visible: bool):
        self._titleVisible = visible
        self._wdgTitle.setVisible(visible)

    def setToolbarVisible(self, visible: bool):
        self.toolbar().setVisible(visible)

    def setMargins(self, left: int, top: int, right: int, bottom: int):
        self.textEdit.setViewportMargins(left, top, right, bottom)

    def setGrammarCheckEnabled(self, enabled: bool):
        self.highlighter.setCheckEnabled(enabled)

    def checkGrammar(self):
        self.highlighter.rehighlight()

    def asyncCheckGrammer(self):
        self.highlighter.asyncRehighlight()

    def clear(self):
        self.textEdit.clear()
        self._textTitle.clear()

    def statistics(self) -> TextStatistics:
        return self.textEdit.statistics()

    def _scrolled(self, value: int):
        if value > self._wdgTitle.height():
            self._wdgTitle.setHidden(True)
        elif self._titleVisible:
            self._wdgTitle.setVisible(True)


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
        if app_env.test_env():
            super(RotatedButton, self).paintEvent(event)
            return
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
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)

        painter.end()

    @overrides
    def sizeHint(self):
        size = super(RotatedButton, self).sizeHint()
        size.transpose()
        return size


class Toggle(AnimatedToggle):
    def __init__(self, parent=None):
        super(Toggle, self).__init__(parent=parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
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
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
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

        self.setFrameStyle(QFrame.Shape.Box)
        hbox(self, 0)
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
        transparent(button)
        button.installEventFilter(self)
        button.setIconSize(QSize(14, 14))
        button.setCursor(Qt.CursorShape.PointingHandCursor)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QToolButton):
            if event.type() == QEvent.Type.Enter:
                watched.setIconSize(QSize(16, 16))
            elif event.type() == QEvent.Type.Leave:
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


class RemovalButton(QToolButton):
    def __init__(self, parent=None, colorOff: str = 'grey', colorOn='red', colorHover='black'):
        super(RemovalButton, self).__init__(parent)
        self._colorOff = colorOff
        self._colorHover = colorHover
        self.setIcon(IconRegistry.close_icon(self._colorOff))
        pointy(self)
        self.installEventFilter(self)
        self.setIconSize(QSize(12, 12))
        transparent(self)

        self.pressed.connect(lambda: self.setIcon(IconRegistry.close_icon(colorOn)))
        self.released.connect(lambda: self.setIcon(IconRegistry.close_icon(colorOff)))

    @overrides
    def eventFilter(self, watched: 'QObject', event: 'QEvent') -> bool:
        if event.type() == QEvent.Type.Enter:
            self.setIcon(IconRegistry.close_icon(self._colorHover))
        elif event.type() == QEvent.Type.Leave:
            self.setIcon(IconRegistry.close_icon(self._colorOff))
        return super(RemovalButton, self).eventFilter(watched, event)


class ButtonsOnlySpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineEdit().setVisible(False)
        self.setFixedWidth(18)
        self.setFrame(False)


class FontSizeSpinBox(QWidget):
    DEFAULT_VALUE: int = 2
    fontChanged = pyqtSignal(int)

    def __init__(self, font_size_prefix: str = "Font Size:"):
        super().__init__()
        self._font_sizes = [8, 10, 12, 13, 14, 16, 18, 20, 24, 28, 32, 48, 64]

        self._label = QLabel(font_size_prefix, self)
        self._font_size_spinner = ButtonsOnlySpinBox(self)
        self._font_size_spinner.setRange(0, len(self._font_sizes) - 1)
        self._font_size_spinner.setValue(self.DEFAULT_VALUE)
        self._font_size_spinner.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)  # Show only up/down buttons
        self._font_size_spinner.valueChanged.connect(self._updateFontSize)

        hbox(self)
        self.layout().addWidget(self._label)
        self.layout().addWidget(self._font_size_spinner)

        self._updateFontSize()

    def setValue(self, value: int):
        try:
            index = self._font_sizes.index(value)
            self._font_size_spinner.setValue(index)
        except ValueError:
            self._font_size_spinner.setValue(self.DEFAULT_VALUE)

    def _updateFontSize(self):
        selected_index = self._font_size_spinner.value()
        font_size = self._font_sizes[selected_index]

        self._label.setText(f"{font_size} pt")

        self.fontChanged.emit(font_size)
