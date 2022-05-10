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
from PyQt5.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QFont, QTextBlockFormat, QTextFormat
from PyQt5.QtWidgets import QTextEdit
from qttextedit import EnhancedTextEdit

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel


def format_manuscript(novel: Novel) -> QTextEdit:
    textedit = EnhancedTextEdit()
    font = QFont('Times New Roman', 12)
    textedit.setFont(font)

    json_client.load_manuscript(novel)

    for i, chapter in enumerate(novel.chapters):
        textedit.textCursor().insertBlock()
        textedit.textCursor().insertText(f'Chapter {i + 1}')
        textedit.textCursor().insertBlock()
        scenes = novel.scenes_in_chapter(chapter)
        for j, scene in enumerate(scenes):
            if not scene.manuscript:
                continue

            document = QTextDocument()
            document.setHtml(scene.manuscript.content)
            document.setDocumentMargin(0)

            cursor: QTextCursor = document.rootFrame().firstCursorPosition()
            cursor.select(QTextCursor.Document)
            format = QTextCharFormat()

            format.setFont(font)
            cursor.mergeCharFormat(format)

            blockFmt = QTextBlockFormat()
            blockFmt.setTextIndent(20)
            blockFmt.setTopMargin(0)
            blockFmt.setBottomMargin(0)
            blockFmt.setLeftMargin(0)
            blockFmt.setRightMargin(0)
            blockFmt.setLineHeight(200, QTextBlockFormat.ProportionalHeight)

            cursor.mergeBlockFormat(blockFmt)
            cursor.clearSelection()

            cursor.insertBlock()

            if j == len(scenes) - 1:
                cursor = document.rootFrame().lastCursorPosition()
                cursor.movePosition(QTextCursor.NextBlock)
                cursor.select(QTextCursor.BlockUnderCursor)
                blockFmt = QTextBlockFormat()
                blockFmt.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
                cursor.mergeBlockFormat(blockFmt)
                cursor.clearSelection()

            textedit.insertHtml(document.toHtml())

    textedit.setViewportMargins(0, 0, 0, 0)

    return textedit
