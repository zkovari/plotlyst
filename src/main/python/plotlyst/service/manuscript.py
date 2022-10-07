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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QFont, QTextBlockFormat, QTextFormat

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Document


def format_manuscript(novel: Novel) -> QTextDocument:
    json_client.load_manuscript(novel)

    font = QFont('Times New Roman', 12)

    chapter_title_block_format = QTextBlockFormat()
    chapter_title_block_format.setAlignment(Qt.AlignmentFlag.AlignCenter)

    block_format = QTextBlockFormat()
    block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
    block_format.setTextIndent(20)
    block_format.setTopMargin(0)
    block_format.setBottomMargin(0)
    block_format.setLeftMargin(0)
    block_format.setRightMargin(0)
    block_format.setLineHeight(150, QTextBlockFormat.ProportionalHeight)

    page_break_format = QTextBlockFormat()
    page_break_format.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysAfter)

    char_format = QTextCharFormat()
    char_format.setFont(font)

    document = QTextDocument()
    document.setDefaultFont(font)
    document.setDocumentMargin(0)

    cursor: QTextCursor = document.rootFrame().firstCursorPosition()

    for i, chapter in enumerate(novel.chapters):
        cursor.insertBlock(chapter_title_block_format)
        cursor.insertText(f'Chapter {i + 1}')

        cursor.insertBlock(block_format)

        scenes = novel.scenes_in_chapter(chapter)
        for j, scene in enumerate(scenes):
            if not scene.manuscript:
                continue

            scene_text_doc = format_document(scene.manuscript, char_format)
            cursor.insertHtml(scene_text_doc.toHtml())
            cursor.insertBlock(block_format)

            if j == len(scenes) - 1 and i != len(novel.chapters) - 1:
                cursor.insertBlock(page_break_format)

    return document


def format_document(doc: Document, char_format: QTextCharFormat) -> QTextDocument:
    text_doc = QTextDocument()
    text_doc.setHtml(doc.content)

    cursor: QTextCursor = text_doc.rootFrame().firstCursorPosition()
    cursor.select(QTextCursor.Document)
    cursor.mergeCharFormat(char_format)
    cursor.clearSelection()

    return text_doc
