"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from typing import Optional

from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QHeaderView
from overrides import overrides

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Document
from src.main.python.plotlyst.events import SceneChangedEvent, SceneDeletedEvent
from src.main.python.plotlyst.model.docs_model import DocumentsTreeModel, DocumentNode
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.notes_view_ui import Ui_NotesView


class DocumentsView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [SceneChangedEvent, SceneDeletedEvent])
        self.ui = Ui_NotesView()
        self.ui.setupUi(self.widget)
        self._current_doc: Optional[Document] = None

        self.model = DocumentsTreeModel(self.novel)
        self.ui.treeDocuments.setModel(self.model)
        self.ui.treeDocuments.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.treeDocuments.setColumnWidth(1, 20)
        self.ui.treeDocuments.clicked.connect(self._doc_clicked)

        self.ui.editor.textEditor.textChanged.connect(self._save)
        self.ui.editor.setHidden(True)

    @overrides
    def refresh(self):
        pass

    def _doc_clicked(self, index: QModelIndex):
        if index.column() == 0:
            self.ui.editor.setVisible(True)
            node: DocumentNode = index.data(DocumentsTreeModel.NodeRole)
            self._current_doc = node.document
            if not node.document.content_loaded:
                json_client.load_document(self.novel, self._current_doc)
            self.ui.editor.textEditor.setHtml(self._current_doc.content)
            self.ui.editor.textEditor.setFocus()

    def _save(self):
        if self._current_doc:
            self._current_doc.content = self.ui.editor.textEditor.toHtml()
            json_client.save_document(self.novel, self._current_doc)
