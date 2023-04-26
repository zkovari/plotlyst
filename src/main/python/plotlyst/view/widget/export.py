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
import pypandoc
from PyQt6.QtWidgets import QDialog

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.service.manuscript import prepare_content_for_convert
from src.main.python.plotlyst.view.generated.export_manuscript_dialog_ui import Ui_ExportManuscriptDialog


class ExportManuscriptDialog(QDialog, Ui_ExportManuscriptDialog):
    def __init__(self, novel: Novel, parent=None):
        super(ExportManuscriptDialog, self).__init__(parent)
        self.setupUi(self)
        self._novel = novel

    def display(self):
        json_client.load_manuscript(self._novel)

        html: str = ''
        for i, chapter in enumerate(self._novel.chapters):
            html += f'<div custom-style="Title">Chapter {i + 1}</div>'
            for j, scene in enumerate(self._novel.scenes_in_chapter(chapter)):
                if not scene.manuscript:
                    continue

                scene_html = prepare_content_for_convert(scene.manuscript.content)
                html += scene_html
                # scene_text_doc = format_document(scene.manuscript, char_format)
                # cursor.insertHtml(scene_text_doc.toHtml())
                # cursor.insertBlock(block_format)
                #
                # if j == len(scenes) - 1 and i != len(novel.chapters) - 1:
                #     cursor.insertBlock(page_break_format)
        # prepare_content_for_convert()
        # html = '''
        # <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
        # <html><head></head>
        # <body>
        # <span custom-style="Title">Title</span>
        # </body>
        # '''
        spec_args = ['--reference-doc', 'custom-reference.docx']
        output = pypandoc.convert_text(html, to='docx', format='html', extra_args=spec_args, outputfile='test.docx')
        # print(output)
        self.exec()


if __name__ == '__main__':
    html = '''
           <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
           <html><head></head>
           <body>
           <div custom-style="Title">Title</div>
           <div custom-style="First Paragraph">Block text.</div>
           <div custom-style="Block Text">Block text.</div>
           Default text.
           <p><b>Bold text</b>
           <p style="color:red;">I am red</p>
           <p><i>Italic text</i>
           </body>
           '''
    spec_args = ['--reference-doc', 'custom-reference.docx']
    output = pypandoc.convert_text(html, to='docx', format='html', extra_args=spec_args, outputfile='test.docx')
    print(output)
