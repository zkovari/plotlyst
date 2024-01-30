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
import datetime
from typing import Optional

import pypandoc
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QFont, QTextBlockFormat, QTextFormat, QTextBlock
from PyQt6.QtWidgets import QFileDialog
from qthandy import ask_confirmation
from slugify import slugify

from plotlyst.core.client import json_client
from plotlyst.core.domain import Novel, Document, DocumentProgress, Scene, DocumentStatistics
from plotlyst.env import open_location, app_env
from plotlyst.resources import resource_registry, ResourceType
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.widget.utility import ask_for_resource


def prepare_content_for_convert(html: str) -> str:
    text_doc = QTextDocument()
    text_doc.setHtml(html)

    block: QTextBlock = text_doc.begin()
    md_content: str = ''
    while block.isValid():
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        md_content += cursor.selection().toMarkdown()

        block = block.next()
    content = pypandoc.convert_text(md_content, to='html', format='md')

    return content


def export_manuscript_to_docx(novel: Novel):
    if not ask_for_resource(ResourceType.PANDOC):
        return

    json_client.load_manuscript(novel)
    if app_env.is_dev():
        target_path = 'test.docx'
    else:
        title = slugify(novel.title if novel.title else 'my-novel')
        target_path, _ = QFileDialog.getSaveFileName(None, 'Export Docx', f'{title}.docx',
                                                     'Docx files (*.docx);;All Files()')
        if not target_path:
            return

    html: str = ''
    for i, chapter in enumerate(novel.chapters):
        html += f'<div custom-style="Title">Chapter {i + 1}</div>'
        for j, scene in enumerate(novel.scenes_in_chapter(chapter)):
            if not scene.manuscript:
                continue

            scene_html = prepare_content_for_convert(scene.manuscript.content)
            html += scene_html

    spec_args = ['--reference-doc', resource_registry.manuscript_docx_template]
    pypandoc.convert_text(html, to='docx', format='html', extra_args=spec_args, outputfile=target_path)

    if ask_confirmation('Export was finished. Open file in editor?'):
        open_location(target_path)


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
    block_format.setLineHeight(150, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)

    page_break_format = QTextBlockFormat()
    page_break_format.setPageBreakPolicy(QTextFormat.PageBreakFlag.PageBreak_AlwaysAfter)

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
    cursor.select(QTextCursor.SelectionType.Document)
    cursor.mergeCharFormat(char_format)
    cursor.clearSelection()

    return text_doc


def today_str() -> str:
    today = datetime.date.today()
    return today.strftime("%Y-%m-%d")


def find_daily_overall_progress(novel: Novel, date: Optional[str] = None) -> Optional[DocumentProgress]:
    if novel.manuscript_progress:
        if date is None:
            date = today_str()
        return novel.manuscript_progress.get(date, None)


def daily_overall_progress(novel: Novel) -> DocumentProgress:
    date = today_str()
    progress = find_daily_overall_progress(novel, date)
    if progress is None:
        progress = DocumentProgress()
        novel.manuscript_progress[date] = progress

        RepositoryPersistenceManager.instance().update_novel(novel)

    return progress


def find_daily_progress(scene: Scene, date: Optional[str] = None) -> Optional[DocumentProgress]:
    if scene.manuscript.statistics is None:
        scene.manuscript.statistics = DocumentStatistics()

    if scene.manuscript.statistics.progress:
        if date is None:
            date = today_str()
        return scene.manuscript.statistics.progress.get(date, None)


def daily_progress(scene: Scene) -> DocumentProgress:
    date = today_str()
    progress = find_daily_progress(scene, date)

    if progress is None:
        progress = DocumentProgress()
        scene.manuscript.statistics.progress[date] = progress

        RepositoryPersistenceManager.instance().update_scene(scene)

    return progress
