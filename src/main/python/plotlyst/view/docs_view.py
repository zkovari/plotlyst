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

from PyQt5.QtCore import QModelIndex, QRect, QPoint
from PyQt5.QtWidgets import QHeaderView, QMenu, QWidgetAction, QListView, QWidget
from overrides import overrides

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Document, doc_characters_id, Character, DocumentType, Causality, \
    CausalityItem
from src.main.python.plotlyst.events import SceneChangedEvent, SceneDeletedEvent
from src.main.python.plotlyst.model.characters_model import CharactersTableModel
from src.main.python.plotlyst.model.common import emit_column_changed_in_tree
from src.main.python.plotlyst.model.docs_model import DocumentsTreeModel, DocumentNode
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import spacer_widget
from src.main.python.plotlyst.view.generated.docs_sidebar_widget_ui import Ui_DocumentsSidebarWidget
from src.main.python.plotlyst.view.generated.notes_view_ui import Ui_NotesView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.causality import CauseAndEffectDiagram
from src.main.python.plotlyst.view.widget.input import RotatedButton


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
        self.ui.treeDocuments.expandAll()
        self.model.modelReset.connect(self.refresh)

        self.ui.textEditor.textEditor.textChanged.connect(self._save)
        self.ui.textEditor.textTitle.textChanged.connect(self._title_changed)
        self.ui.textEditor.setHidden(True)

        self.ui.btnAdd.setIcon(IconRegistry.plus_icon())
        self.ui.btnAdd.clicked.connect(self._add_doc)
        self.ui.btnRemove.setIcon(IconRegistry.minus_icon())
        self.ui.btnRemove.clicked.connect(self._remove_doc)

    @overrides
    def refresh(self):
        self.ui.treeDocuments.expandAll()
        self.ui.btnRemove.setEnabled(False)

    def _add_doc(self, parent: Optional[QModelIndex] = None, character: Optional[Character] = None,
                 doc_type: DocumentType = DocumentType.DOCUMENT):
        doc = Document('New Document', type=doc_type)
        if character:
            doc.title = ''
            doc.character_id = character.id
        if doc_type == DocumentType.CAUSE_AND_EFFECT or doc_type == DocumentType.REVERSED_CAUSE_AND_EFFECT:
            casuality = Causality(items=[CausalityItem('Story ending')])
            doc.data = casuality
            doc.data_id = casuality.id
            json_client.save_document(self.novel, doc)

        doc.loaded = True

        if parent:
            index = self.model.insertDocUnder(doc, parent)
        else:
            index = self.model.insertDoc(doc)
        self.ui.treeDocuments.select(index)
        self.ui.btnRemove.setEnabled(True)
        self._edit(index)

    def _doc_clicked(self, index: QModelIndex):
        node: DocumentNode = index.data(DocumentsTreeModel.NodeRole)
        self.ui.btnRemove.setEnabled(node.document.id != doc_characters_id)
        if index.column() == 0:
            self._edit(index)
        elif index.column() == 1:
            self._show_docs_popup(index)

    def _show_docs_popup(self, index: QModelIndex):
        def add_character(char_index: QModelIndex):
            char = char_index.data(CharactersTableModel.CharacterRole)
            self._add_doc(index, character=char)

        rect: QRect = self.ui.treeDocuments.visualRect(index)
        menu = QMenu(self.ui.treeDocuments)
        menu.addAction(IconRegistry.document_edition_icon(), 'Document', lambda: self._add_doc(index))

        character_menu = QMenu('Characters', menu)
        character_menu.setIcon(IconRegistry.character_icon())
        action = QWidgetAction(character_menu)
        _view = QListView()
        _view.clicked.connect(add_character)
        action.setDefaultWidget(_view)
        _view.setModel(CharactersTableModel(self.novel))
        character_menu.addAction(action)
        menu.addMenu(character_menu)

        menu.addAction(IconRegistry.reversed_cause_and_effect_icon(), 'Reversed Cause and Effect',
                       lambda: self._add_doc(index, doc_type=DocumentType.REVERSED_CAUSE_AND_EFFECT))

        menu.popup(self.ui.treeDocuments.viewport().mapToGlobal(QPoint(rect.x(), rect.y())))

    def _remove_doc(self):
        selected = self.ui.treeDocuments.selectionModel().selectedIndexes()
        if not selected:
            return
        self.model.removeDoc(selected[0])
        self.ui.textEditor.setVisible(False)

    def _edit(self, index: QModelIndex):
        node: DocumentNode = index.data(DocumentsTreeModel.NodeRole)
        self._current_doc = node.document

        if not self._current_doc.loaded:
            json_client.load_document(self.novel, self._current_doc)

        char = node.document.character(self.novel)

        if self._current_doc.type == DocumentType.DOCUMENT:
            self.ui.stackedEditor.setCurrentWidget(self.ui.docEditorPage)
            self.ui.textEditor.setVisible(True)
            if char:
                self.ui.textEditor.setText(self._current_doc.content, char.name, title_read_only=True)
            else:
                self.ui.textEditor.setText(self._current_doc.content, self._current_doc.title)
        else:
            self.ui.stackedEditor.setCurrentWidget(self.ui.customEditorPage)
            while self.ui.customEditorPage.layout().count():
                item = self.ui.customEditorPage.layout().takeAt(0)
                item.widget().deleteLater()
            if self._current_doc.type == DocumentType.REVERSED_CAUSE_AND_EFFECT:
                widget = CauseAndEffectDiagram(self._current_doc.data, reversed_=True)
                widget.model.changed.connect(self._save)
                self.ui.customEditorPage.layout().addWidget(widget)

    def _save(self):
        if not self._current_doc:
            return
        if self._current_doc.type == DocumentType.DOCUMENT:
            self._current_doc.content = self.ui.textEditor.textEditor.toHtml()
        json_client.save_document(self.novel, self._current_doc)

    def _title_changed(self):
        if self._current_doc:
            new_title = self.ui.textEditor.textTitle.toPlainText()
            if new_title and new_title != self._current_doc.title:
                self._current_doc.title = new_title
                emit_column_changed_in_tree(self.model, 0, QModelIndex())
                self.repo.update_novel(self.novel)


class DocumentsSidebar(QWidget, AbstractNovelView, Ui_DocumentsSidebarWidget):

    def __init__(self, novel: Novel, parent=None):
        super(DocumentsSidebar, self).__init__(parent)
        self.novel = novel
        self.setupUi(self)
        self._updateDocs()

    @overrides
    def refresh(self):
        self._updateDocs()

    def _updateDocs(self):
        while self.scrollAreaWidgetContents.layout().count():
            item = self.scrollAreaWidgetContents.layout().takeAt(0)
            item.widget().deleteLater()
        for doc in self.novel.documents:
            btn = RotatedButton()
            btn.setText(doc.title)
            self.scrollAreaWidgetContents.layout().addWidget(btn)
        self.scrollAreaWidgetContents.layout().addWidget(spacer_widget(vertical=True))
