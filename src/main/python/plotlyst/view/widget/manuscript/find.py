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
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QShowEvent, QTextDocument, QTextCursor, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtWidgets import QWidget, QTextBrowser
from overrides import overrides
from qthandy import incr_font, vbox, busy, transparent

from plotlyst.common import PLOTLYST_TERTIARY_COLOR
from plotlyst.core.client import json_client
from plotlyst.core.domain import Novel
from plotlyst.view.common import DelayedSignalSlotConnector
from plotlyst.view.widget.input import SearchField


class SearchHighlighter(QSyntaxHighlighter):
    def __init__(self, search_term: str, document: QTextDocument):
        super().__init__(document)
        self.search_term = search_term
        self.format = QTextCharFormat()
        self.format.setBackground(QColor(PLOTLYST_TERTIARY_COLOR))
        self.format.setForeground(QColor('black'))

    @overrides
    def highlightBlock(self, text: str):
        if not self.search_term:
            return

        pattern = QRegularExpression(self.search_term)
        match_iter = pattern.globalMatch(text)

        while match_iter.hasNext():
            match = match_iter.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.format)


class SearchResultsTextEdit(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        transparent(self)
        # self.setMouseTracking(True)

    # @overrides
    # def enterEvent(self, event: QEnterEvent) -> None:
    #     self.setCursor(Qt.CursorShape.PointingHandCursor)
    #     pass
    #
    # @overrides
    # def mouseMoveEvent(self, event: QMouseEvent) -> None:
    #     self.setCursor(Qt.CursorShape.PointingHandCursor)


class ManuscriptFindWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        vbox(self)

        self.search = SearchField()
        incr_font(self.search.lineSearch)
        DelayedSignalSlotConnector(self.search.lineSearch.textEdited, self._search, delay=500, parent=self)

        self.wdgResults = SearchResultsTextEdit()

        self.layout().addWidget(self.search, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.wdgResults)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.search.lineSearch.setFocus()

    @busy
    def _search(self, term: str):
        self.wdgResults.clear()
        json_client.load_manuscript(self.novel)
        font = self.wdgResults.font()
        font.setPointSize(11)
        self.wdgResults.setFont(font)

        results = []
        html_result = "<html><body>"
        context_size = 30

        for scene in self.novel.scenes:
            if not scene.manuscript:
                continue
            doc = QTextDocument()
            doc.setHtml(scene.manuscript.content)

            cursor = QTextCursor(doc)
            raw_text = doc.toPlainText()
            scene_matches = []
            while not cursor.isNull() and not cursor.atEnd():
                cursor = doc.find(term, cursor)
                if cursor.isNull():
                    break

                start = cursor.selectionStart()
                end = cursor.selectionEnd()

                before_start = raw_text.rfind(" ", 0, start - context_size) + 1
                after_end = raw_text.find(" ", end + context_size)
                if after_end == -1:
                    after_end = len(raw_text)

                before = raw_text[before_start:start]
                after = raw_text[end:after_end]
                match_text = raw_text[start:end]

                formatted_match = f'{before}<span style="background-color: {PLOTLYST_TERTIARY_COLOR}; color: black; padding: 2px;">{match_text}</span>{after}'

                scene_matches.append({
                    "scene": scene.title_or_index(self.novel),
                    "start": start,
                    "end": end,
                    "match": match_text,
                    "context": formatted_match
                })

            if scene_matches:
                results.extend(scene_matches)

                html_result += f'<h3>{scene.title_or_index(self.novel)}</h3>'
                for match in scene_matches:
                    html_result += f'<p>{match["context"]}</p>'

        html_result += "</body></html>"
        self.wdgResults.clear()
        self.wdgResults.setHtml(html_result)
        # self.highlighter = SearchHighlighter(term, self.wdgResults.document())
