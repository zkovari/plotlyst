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
from PyQt5.QtGui import QTextDocument, QTextCursor, QTextCharFormat
from PyQt5.QtPrintSupport import QPrintPreviewDialog
from qttextedit import EnhancedTextEdit

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel


class ManuscriptPreviewDialog(QPrintPreviewDialog):
    def __init__(self, parent=None):
        super(ManuscriptPreviewDialog, self).__init__(parent)

    def display(self, novel: Novel):
        if not novel:
            return
        textedit = EnhancedTextEdit()
        if not novel.scenes[0].manuscript.loaded:
            json_client.load_document(novel, novel.scenes[0].manuscript)

        document = QTextDocument()
        document.setHtml(novel.scenes[0].manuscript.content)
        cursor: QTextCursor = document.rootFrame().firstCursorPosition()
        cursor.select(QTextCursor.Document)
        format = QTextCharFormat()
        format.setFontPointSize(8)
        cursor.mergeCharFormat(format)
        cursor.clearSelection()

        textedit.insertHtml(document.toHtml())
        self.paintRequested.connect(textedit.print)
        self.exec()
