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
from PyQt5.QtWidgets import QHeaderView, QMenu, QWidgetAction, QListView, QWidget, QStylePainter, QStyle, \
    QStyleOptionButton, QPushButton
from overrides import overrides

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Document, doc_characters_id, Character
from src.main.python.plotlyst.events import SceneChangedEvent, SceneDeletedEvent
from src.main.python.plotlyst.model.characters_model import CharactersTableModel
from src.main.python.plotlyst.model.common import emit_column_changed_in_tree
from src.main.python.plotlyst.model.docs_model import DocumentsTreeModel, DocumentNode
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import spacer_widget
from src.main.python.plotlyst.view.generated.docs_sidebar_widget_ui import Ui_DocumentsSidebarWidget
from src.main.python.plotlyst.view.generated.notes_view_ui import Ui_NotesView
from src.main.python.plotlyst.view.icons import IconRegistry


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

        self.ui.editor.textEditor.textChanged.connect(self._save)
        self.ui.editor.textTitle.textChanged.connect(self._title_changed)
        self.ui.editor.setHidden(True)

        self.ui.btnAdd.setIcon(IconRegistry.plus_icon())
        self.ui.btnAdd.clicked.connect(self._add_doc)
        self.ui.btnRemove.setIcon(IconRegistry.minus_icon())
        self.ui.btnRemove.clicked.connect(self._remove_doc)

    @overrides
    def refresh(self):
        self.ui.treeDocuments.expandAll()
        self.ui.btnRemove.setEnabled(False)

    def _add_doc(self, parent: Optional[QModelIndex] = None, character: Optional[Character] = None):
        doc = Document('New Document')
        if character:
            doc.title = ''
            doc.character_id = character.id

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
            if node.document.id == doc_characters_id or 'character' in node.document.title.lower():
                self._show_characters_popup(index)
            else:
                self._add_doc(index)

    def _show_characters_popup(self, index: QModelIndex):
        def add_character(char_index: QModelIndex):
            char = char_index.data(CharactersTableModel.CharacterRole)
            self._add_doc(index, character=char)

        rect: QRect = self.ui.treeDocuments.visualRect(index)
        menu = QMenu(self.ui.treeDocuments)
        action = QWidgetAction(menu)
        _view = QListView()
        _view.clicked.connect(add_character)
        action.setDefaultWidget(_view)
        _view.setModel(CharactersTableModel(self.novel))
        menu.addAction(action)
        menu.addAction(IconRegistry.plus_circle_icon(), 'Add Custom...', lambda: self._add_doc(index))

        menu.popup(self.ui.treeDocuments.viewport().mapToGlobal(QPoint(rect.x(), rect.y())))

    def _remove_doc(self):
        selected = self.ui.treeDocuments.selectionModel().selectedIndexes()
        if not selected:
            return
        self.model.removeDoc(selected[0])
        self.ui.editor.setVisible(False)

    def _edit(self, index: QModelIndex):
        self.ui.editor.setVisible(True)
        node: DocumentNode = index.data(DocumentsTreeModel.NodeRole)
        self._current_doc = node.document
        if not node.document.content_loaded:
            json_client.load_document(self.novel, self._current_doc)
        char = node.document.character(self.novel)
        if char:
            self.ui.editor.setText(self._current_doc.content, char.name)
        else:
            self.ui.editor.setText(self._current_doc.content, self._current_doc.title)

    def _save(self):
        if self._current_doc:
            self._current_doc.content = self.ui.editor.textEditor.toHtml()
            json_client.save_document(self.novel, self._current_doc)

    def _title_changed(self):
        if self._current_doc:
            new_title = self.ui.editor.textTitle.toPlainText()
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


class RotatedButton(QPushButton):
    def __init__(self, parent=None):
        super(RotatedButton, self).__init__(parent)

    @overrides
    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        painter.rotate(90)
        painter.translate(0, -1 * self.width())
        option.rect = option.rect.transposed()
        painter.drawControl(QStyle.CE_PushButton, option)

    def sizeHint(self):
        size = super(RotatedButton, self).sizeHint()
        size.transpose()
        return size
