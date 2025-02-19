"""
Plotlyst
Copyright (C) 2021-2025  Zsolt Kovari

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
from functools import partial
from typing import Optional, List

from PyQt6 import QtGui
from PyQt6.QtCore import pyqtSignal, QTextBoundaryFinder, Qt
from PyQt6.QtGui import QFont, QResizeEvent, QShowEvent, QTextCursor, QTextCharFormat, QSyntaxHighlighter, QColor, \
    QTextBlock
from PyQt6.QtWidgets import QWidget, QApplication, QTextEdit
from overrides import overrides
from qthandy import vbox, clear_layout, vspacer, margins, transparent, gc
from qttextedit import remove_font, TextBlockState
from qttextedit.ops import Heading1Operation, Heading2Operation, Heading3Operation, InsertListOperation, \
    InsertNumberedListOperation, BoldOperation, ItalicOperation, UnderlineOperation, StrikethroughOperation, \
    AlignLeftOperation, AlignCenterOperation, AlignRightOperation

from plotlyst.common import RELAXED_WHITE_COLOR, DEFAULT_MANUSCRIPT_LINE_SPACE, DEFAULT_MANUSCRIPT_INDENT
from plotlyst.core.client import json_client
from plotlyst.core.domain import DocumentProgress, Novel, Scene, TextStatistics, DocumentStatistics, FontSettings
from plotlyst.env import app_env
from plotlyst.service.manuscript import daily_progress, daily_overall_progress
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.widget.input import BasePopupTextEditorToolbar, TextEditBase, GrammarHighlighter, \
    GrammarHighlightStyle


class SentenceHighlighter(QSyntaxHighlighter):
    DEFAULT_FOREGROUND_COLOR = '#dee2e6'

    def __init__(self, textedit: QTextEdit):
        super(SentenceHighlighter, self).__init__(textedit.document())
        self._editor = textedit
        self._sentenceEnabled: bool = False

        self._hidden_format = QTextCharFormat()
        self._hidden_format.setForeground(QColor(self.DEFAULT_FOREGROUND_COLOR))

        self._visible_format = QTextCharFormat()
        self._visible_format.setForeground(QColor(RELAXED_WHITE_COLOR))

        self._prevBlock: Optional[QTextBlock] = None
        self._editor.cursorPositionChanged.connect(self.rehighlight)

    def setSentenceHighlightEnabled(self, enabled: bool):
        self._sentenceEnabled = enabled
        self._hidden_format.setForeground(QColor('#38414A' if enabled else self.DEFAULT_FOREGROUND_COLOR))
        self.rehighlight()

    @overrides
    def highlightBlock(self, text: str) -> None:
        self.setFormat(0, len(text), self._hidden_format)
        if self._sentenceEnabled and self._editor.textCursor().block() == self.currentBlock():
            text = self._editor.textCursor().block().text()
            finder = QTextBoundaryFinder(QTextBoundaryFinder.BoundaryType.Sentence, text)
            pos = self._editor.textCursor().positionInBlock()
            boundary = finder.toNextBoundary()
            prev_boundary = 0
            while -1 < boundary < pos:
                prev_boundary = boundary
                boundary = finder.toNextBoundary()

            self.setFormat(prev_boundary, boundary - prev_boundary, self._visible_format)


class ManuscriptPopupTextEditorToolbar(BasePopupTextEditorToolbar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty('rounded', True)
        self.setProperty('relaxed-white-bg', True)
        margins(self, 5, 5, 5, 5)

        self.addTextEditorOperation(BoldOperation)
        self.addTextEditorOperation(ItalicOperation)
        self.addTextEditorOperation(UnderlineOperation)
        self.addTextEditorOperation(StrikethroughOperation)
        self.addSeparator()
        self.addTextEditorOperation(AlignLeftOperation)
        self.addTextEditorOperation(AlignCenterOperation)
        self.addTextEditorOperation(AlignRightOperation)
        self.addSeparator()
        self.addTextEditorOperation(InsertListOperation)
        self.addTextEditorOperation(InsertNumberedListOperation)


class ManuscriptTextEdit(TextEditBase):
    sceneSeparatorClicked = pyqtSignal(Scene)

    def __init__(self, parent=None):
        super(ManuscriptTextEdit, self).__init__(parent)
        self._pasteAsOriginalEnabled = False
        self._resizedOnShow: bool = False
        self._minHeight = 40
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTabChangesFocus(True)

        self.highlighter = GrammarHighlighter(self.document(), checkEnabled=False,
                                              highlightStyle=GrammarHighlightStyle.BACKGOUND)

        self._sentenceHighlighter: Optional[SentenceHighlighter] = None

        toolbar = ManuscriptPopupTextEditorToolbar()
        toolbar.activate(self)
        self.setPopupWidget(toolbar)

        # self._sceneSepBlockFormat = QTextBlockFormat()
        # self._sceneSepBlockFormat.setTextIndent(40)
        # self._sceneSepBlockFormat.setTopMargin(20)
        # self._sceneSepBlockFormat.setBottomMargin(20)

        # self._sceneTextObject = SceneSeparatorTextObject(self)
        # self.document().documentLayout().registerHandler(SceneSeparatorTextFormat, self._sceneTextObject)

        self._setDefaultStyleSheet()
        self.setCommandOperations([Heading1Operation, Heading2Operation, Heading3Operation, InsertListOperation,
                                   InsertNumberedListOperation])

        self.textChanged.connect(self.resizeToContent)

    @overrides
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        cursor: QTextCursor = self.textCursor()
        if cursor.atBlockEnd() and event.key() == Qt.Key.Key_Space:
            cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter, QTextCursor.MoveMode.KeepAnchor)
            if cursor.selectedText() == ' ':
                self.textCursor().deletePreviousChar()
                self.textCursor().insertText('.')
        super(ManuscriptTextEdit, self).keyPressEvent(event)

    # @overrides
    # def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
    #     anchor = self.anchorAt(event.pos())
    #     if anchor and anchor.startswith(SceneSeparatorTextFormatPrefix):
    #         if QApplication.overrideCursor() is None:
    #             QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
    #         synopsis = self._sceneTextObject.sceneSynopsis(anchor.replace(SceneSeparatorTextFormatPrefix, ''))
    #         self.setToolTip(synopsis)
    #         return
    #     else:
    #         QApplication.restoreOverrideCursor()
    #         self.setToolTip('')
    #     super(ManuscriptTextEdit, self).mouseMoveEvent(event)

    # @overrides
    # def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
    #     anchor = self.anchorAt(event.pos())
    #     if anchor and anchor.startswith(SceneSeparatorTextFormatPrefix):
    #         scene = self._sceneTextObject.scene(anchor.replace(SceneSeparatorTextFormatPrefix, ''))
    #         if scene:
    #             self.sceneSeparatorClicked.emit(scene)
    #         return
    #
    #     super(ManuscriptTextEdit, self).mouseReleaseEvent(event)

    def setGrammarCheckEnabled(self, enabled: bool):
        self.highlighter.setCheckEnabled(enabled)

    def checkGrammar(self):
        self.highlighter.rehighlight()

    def asyncCheckGrammar(self):
        self.highlighter.asyncRehighlight()

    def initSentenceHighlighter(self):
        transparent(self)
        self._sentenceHighlighter = SentenceHighlighter(self)

    def clearSentenceHighlighter(self):
        if self._sentenceHighlighter is not None:
            gc(self._sentenceHighlighter)
            self._sentenceHighlighter = None

        self._setDefaultStyleSheet()

    def setSentenceHighlighterEnabled(self, enabled: bool):
        self._sentenceHighlighter.setSentenceHighlightEnabled(enabled)

    def setScene(self, scene: Scene):
        # self._sceneTextObject.setScenes([scene])

        self._addScene(scene)
        self.setUneditableBlocksEnabled(False)
        self.document().clearUndoRedoStacks()
        self.resizeToContent()

    # def setScenes(self, scenes: List[Scene]):
    #     def sceneCharFormat(scene: Scene) -> QTextCharFormat:
    #         sceneSepCharFormat = QTextCharFormat()
    #         sceneSepCharFormat.setObjectType(SceneSeparatorTextFormat)
    #         sceneSepCharFormat.setToolTip(scene.synopsis)
    #         sceneSepCharFormat.setAnchor(True)
    #         sceneSepCharFormat.setAnchorHref(f'{SceneSeparatorTextFormatPrefix}{scene.id}')
    #
    #         return sceneSepCharFormat
    #
    #     self.setUneditableBlocksEnabled(True)
    #     self._sceneTextObject.setScenes(scenes)
    #
    #     for i, scene in enumerate(scenes):
    #         self.textCursor().insertBlock(self._sceneSepBlockFormat)
    #         self.textCursor().insertText(f'{OBJECT_REPLACEMENT_CHARACTER}', sceneCharFormat(scene))
    #         self.textCursor().block().setUserState(TextBlockState.UNEDITABLE.value)
    #         self.insertNewBlock()
    #         self._addScene(scene)
    #
    #     self._deleteBlock(0, force=True)
    #
    #     self.document().clearUndoRedoStacks()
    #     self.resizeToContent()

    # def insertNewBlock(self):
    #     self.textCursor().insertBlock(self._defaultBlockFormat, QTextCharFormat())

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self._resizedOnShow:
            self.resizeToContent()
            self._resizedOnShow = True

    @overrides
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._resizedOnShow:
            self.resizeToContent()

    def resizeToContent(self):
        padding = self.contentsMargins().top() + self.contentsMargins().bottom() + 2 * self.document().documentMargin()
        size = self.document().size()
        self.setFixedHeight(max(self._minHeight, math.ceil(size.height() + padding)))

    def _addScene(self, scene: Scene):
        if not scene.manuscript.loaded:
            json_client.load_document(app_env.novel, scene.manuscript)

        first_scene_block = self.textCursor().block()
        self.textCursor().insertHtml(remove_font(scene.manuscript.content))
        if first_scene_block.userState() == TextBlockState.UNEDITABLE.value:
            first_scene_block.setUserState(-1)

    def _transparent(self):
        border = 0
        self.setStyleSheet(f'border-top: {border}px dashed {RELAXED_WHITE_COLOR}; background-color: rgba(0, 0, 0, 0);')

    def _setDefaultStyleSheet(self):
        self.setStyleSheet(
            f'ManuscriptTextEdit {{background-color: {RELAXED_WHITE_COLOR};}}')


class ManuscriptEditor(QWidget):
    textChanged = pyqtSignal()
    progressChanged = pyqtSignal(DocumentProgress)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel: Optional[Novel] = None
        self._margins: int = 30
        self._scenes: List[ManuscriptTextEdit] = []
        self._font = self.defaultFont()
        self._characterWidth: int = 40

        vbox(self, 0, 0)

        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        if self._maxContentWidth > 0:
            self._resizeToCharacterWidth()

    def defaultFont(self) -> QFont:
        if app_env.is_linux():
            return QFont('Palatino', 14)
        elif app_env.is_mac():
            return QFont('Palatino', 16)
        elif app_env.is_windows():
            return QFont('Georgia', 16)
        else:
            font = QApplication.font()
            font.setPointSize(16)
            return font

    def setNovel(self, novel: Novel):
        self._novel = novel

        if app_env.platform() in self._novel.prefs.manuscript.font.keys():
            fontSettings = self._getFontSettings()
            if fontSettings.family:
                self._font.setFamily(fontSettings.family)
            if fontSettings.font_size:
                self._font.setPointSize(fontSettings.font_size)
            if fontSettings.text_width:
                self.setCharacterWidth(fontSettings.text_width)
        else:
            self.setCharacterWidth(60)

    def setCharacterWidth(self, width: int):
        self._characterWidth = width
        metrics = QtGui.QFontMetricsF(self.font())
        self._maxContentWidth = metrics.boundingRect('M' * self._characterWidth).width()
        self._resizeToCharacterWidth()

    def setScenes(self, scenes: List[Scene], title: Optional[str] = None):
        self._scenes.clear()
        clear_layout(self)

        for scene in scenes:
            wdg = self._initTextEdit()
            wdg.setScene(scene)
            wdg.textChanged.connect(partial(self._textChanged, wdg, scene))
            self._scenes.append(wdg)
            self.layout().addWidget(wdg)

        self.layout().addWidget(vspacer())

    def statistics(self) -> TextStatistics:
        overall_stats = TextStatistics(0)
        if self.hasScenes():
            for editor in self._scenes:
                overall_stats.word_count += editor.statistics().word_count

        return overall_stats

    def hasScenes(self) -> bool:
        return len(self._scenes) > 0

    def _textChanged(self, textedit: ManuscriptTextEdit, scene: Scene):
        if scene.manuscript.statistics is None:
            scene.manuscript.statistics = DocumentStatistics()

        wc = textedit.statistics().word_count
        updated_progress = self._updateProgress(scene, wc)

        scene.manuscript.content = textedit.toHtml()
        self.repo.update_doc(app_env.novel, scene.manuscript)
        if updated_progress:
            self.repo.update_scene(scene)
            self.repo.update_novel(self._novel)

        self.textChanged.emit()

    def _updateProgress(self, scene: Scene, wc: int) -> bool:
        if scene.manuscript.statistics.wc == wc:
            return False

        diff = wc - scene.manuscript.statistics.wc
        progress: DocumentProgress = daily_progress(scene)
        overall_progress = daily_overall_progress(self._novel)
        if diff > 0:
            progress.added += diff
            overall_progress.added += diff
        else:
            progress.removed += abs(diff)
            overall_progress.removed += abs(diff)
        self.progressChanged.emit(overall_progress)
        scene.manuscript.statistics.wc = wc

        return True

    def _initTextEdit(self) -> ManuscriptTextEdit:
        _textedit = ManuscriptTextEdit()
        _textedit.setFont(self._font)
        _textedit.setDashInsertionMode(self._novel.prefs.manuscript.dash)
        _textedit.setAutoCapitalizationMode(self._novel.prefs.manuscript.capitalization)

        _textedit.zoomIn(int(_textedit.font().pointSize() * 0.25))
        _textedit.setBlockFormat(DEFAULT_MANUSCRIPT_LINE_SPACE, textIndent=DEFAULT_MANUSCRIPT_INDENT)
        _textedit.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoNone)
        # _textedit.selectionChanged.connect(self.selectionChanged.emit)
        _textedit.setProperty('borderless', True)

        _textedit.setPlaceholderText('Write your story...')
        _textedit.setSidebarEnabled(False)
        _textedit.setReadOnly(self._novel.is_readonly())
        # _textedit.setViewportMargins(0, 0, 0, 0)
        _textedit.setDocumentMargin(0)

        return _textedit

    def _getFontSettings(self) -> FontSettings:
        if app_env.platform() not in self._novel.prefs.manuscript.font.keys():
            self._novel.prefs.manuscript.font[app_env.platform()] = FontSettings()
        return self._novel.prefs.manuscript.font[app_env.platform()]

    def _resizeToCharacterWidth(self):
        # print(f'max {self._maxContentWidth} width {self.width()}')
        if 0 < self._maxContentWidth < self.width():
            margin = self.width() - self._maxContentWidth
        else:
            margin = 0

        margin = int(margin // 2)
        # print(margin)
        margins(self, left=margin, right=margin)
        # current_margins: QMargins = self.viewportMargins()
        # self.setViewportMargins(margin, current_margins.top(), margin, current_margins.bottom())
        # self.resizeToContent()
