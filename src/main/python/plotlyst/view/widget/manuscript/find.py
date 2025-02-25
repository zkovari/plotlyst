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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShowEvent, QTextDocument, QTextCursor
from PyQt6.QtWidgets import QWidget, QTextEdit
from overrides import overrides
from qthandy import incr_font, vbox, busy, transparent

from plotlyst.core.client import json_client
from plotlyst.core.domain import Novel
from plotlyst.view.common import DelayedSignalSlotConnector
from plotlyst.view.widget.input import SearchField


class ManuscriptFindWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        vbox(self)

        self.search = SearchField()
        incr_font(self.search.lineSearch)
        DelayedSignalSlotConnector(self.search.lineSearch.textEdited, self._search, delay=500, parent=self)

        self.wdgResults = QTextEdit()
        transparent(self.wdgResults)

        self.layout().addWidget(self.search, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.wdgResults)

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.search.lineSearch.setFocus()

    @busy
    def _search(self, term: str):
        json_client.load_manuscript(self.novel)
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

                scene_matches.append({
                    "scene": scene.title_or_index(self.novel),
                    "start": start,
                    "end": end,
                    "match": match_text,
                    "context": f"{before}[{match_text}]{after}"
                })

            if scene_matches:
                results.extend(scene_matches)

                html_result += f'<h3>{scene.title_or_index(self.novel)}</h3>'
                for match in scene_matches:
                    html_result += f'<p>{match["context"]}</p>'

        html_result += "</body></html>"
        self.wdgResults.clear()
        self.wdgResults.setHtml(html_result)
