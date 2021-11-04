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
from src.main.python.plotlyst.events import NovelUpdatedEvent, SceneChangedEvent
from src.main.python.plotlyst.model.chapters_model import ChaptersTreeModel, SceneNode, ChapterNode
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.manuscript_view_ui import Ui_ManuscriptView


class ManuscriptView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [NovelUpdatedEvent, SceneChangedEvent])
        self.ui = Ui_ManuscriptView()
        self.ui.setupUi(self.widget)
        self._current_doc: Optional[Document] = None
        self.ui.splitter.setSizes([100, 500])
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEmpty)

        self.ui.textEdit.setTitleVisible(False)
        self.ui.textEdit.setToolbarVisible(False)
        self.ui.textEdit.setMargins(30, 30, 30, 30)
        self.ui.textEdit.setFormat(130)

        self.chaptersModel = ChaptersTreeModel(self.novel)
        self.ui.treeChapters.setModel(self.chaptersModel)
        self.ui.treeChapters.expandAll()
        self.chaptersModel.modelReset.connect(self.ui.treeChapters.expandAll)
        self.ui.treeChapters.setColumnWidth(1, 20)
        self.ui.treeChapters.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.treeChapters.clicked.connect(self._edit)

        self.ui.textEdit.textEditor.textChanged.connect(self._save)

    @overrides
    def refresh(self):
        self.chaptersModel.modelReset.emit()

    def _edit(self, index: QModelIndex):
        node = index.data(ChaptersTreeModel.NodeRole)
        if isinstance(node, SceneNode):
            if not node.scene.manuscript:
                node.scene.manuscript = Document('', scene_id=node.scene.id)
                self.repo.update_scene(node.scene)
            self._current_doc = node.scene.manuscript

            if not self._current_doc.loaded:
                json_client.load_document(self.novel, self._current_doc)

            self.ui.stackedWidget.setCurrentWidget(self.ui.pageText)
            self.ui.textEdit.setText(self._current_doc.content, self._current_doc.title)
        elif isinstance(node, ChapterNode):
            self.ui.stackedWidget.setCurrentWidget(self.ui.pageEmpty)

    def _save(self):
        if not self._current_doc:
            return
        self._current_doc.content = self.ui.textEdit.textEditor.toHtml()
        json_client.save_document(self.novel, self._current_doc)
