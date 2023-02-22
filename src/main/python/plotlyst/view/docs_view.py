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
from typing import Optional

from overrides import overrides
from qthandy import clear_layout, bold, btn_popup_menu

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Document, DocumentType
from src.main.python.plotlyst.events import SceneChangedEvent, SceneDeletedEvent
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.doc.mice import MiceQuotientDoc
from src.main.python.plotlyst.view.generated.notes_view_ui import Ui_NotesView
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.causality import CauseAndEffectDiagram
from src.main.python.plotlyst.view.widget.doc.browser import DocumentAdditionMenu
from src.main.python.plotlyst.view.widget.input import DocumentTextEditor


class DocumentsView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [SceneChangedEvent, SceneDeletedEvent])
        self.ui = Ui_NotesView()
        self.ui.setupUi(self.widget)
        self._current_doc: Optional[Document] = None

        self.ui.splitter.setSizes([150, 500])

        self.ui.btnDocuments.setIcon(IconRegistry.document_edition_icon())
        bold(self.ui.lblTitle)

        self.ui.treeDocuments.setNovel(self.novel)
        self.ui.treeDocuments.documentSelected.connect(self._edit)
        self.ui.treeDocuments.documentDeleted.connect(self._clear_text_editor)
        self.ui.treeDocuments.documentIconChanged.connect(self._icon_changed)

        self.textEditor: Optional[DocumentTextEditor] = None

        self.ui.btnAdd.setIcon(IconRegistry.plus_icon('white'))
        self.ui.btnAdd.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnAdd))
        menu = DocumentAdditionMenu(self.novel)
        menu.documentTriggered.connect(self._add_doc)
        btn_popup_menu(self.ui.btnAdd, menu)

    @overrides
    def refresh(self):
        self.ui.treeDocuments.refresh()

    def _add_doc(self, doc: Document):
        self.ui.treeDocuments.addDocument(doc)
        self._edit(doc)

    def _init_text_editor(self):
        self._clear_text_editor()

        self.textEditor = DocumentTextEditor(self.ui.docEditorPage)
        self.ui.docEditorPage.layout().addWidget(self.textEditor)
        self.textEditor.textEdit.textChanged.connect(self._save)
        self.textEditor.titleChanged.connect(self._title_changed)

    def _clear_text_editor(self):
        clear_layout(self.ui.docEditorPage.layout())

    def _edit(self, doc: Document):
        self._init_text_editor()
        self._current_doc = doc

        if not self._current_doc.loaded:
            json_client.load_document(self.novel, self._current_doc)

        char = doc.character(self.novel)

        if self._current_doc.type in [DocumentType.DOCUMENT, DocumentType.STORY_STRUCTURE]:
            self.ui.stackedEditor.setCurrentWidget(self.ui.docEditorPage)
            self.textEditor.setGrammarCheckEnabled(False)
            if char:
                self.textEditor.setText(self._current_doc.content, char.name, icon=avatars.avatar(char),
                                        title_read_only=True)
            else:
                if self._current_doc.icon:
                    icon = IconRegistry.from_name(self._current_doc.icon, self._current_doc.icon_color)
                else:
                    icon = None
                self.textEditor.setText(self._current_doc.content, self._current_doc.title, icon)
            if self.novel.prefs.docs.grammar_check:
                self.textEditor.setGrammarCheckEnabled(True)
                self.textEditor.asyncCheckGrammer()
        else:
            self.ui.stackedEditor.setCurrentWidget(self.ui.customEditorPage)
            clear_layout(self.ui.customEditorPage)
            if self._current_doc.type == DocumentType.REVERSED_CAUSE_AND_EFFECT:
                widget = CauseAndEffectDiagram(self._current_doc.data, reversed_=True)
                widget.model.changed.connect(self._save)
            elif self._current_doc.type == DocumentType.MICE:
                widget = MiceQuotientDoc(self._current_doc, self._current_doc.data)
                widget.changed.connect(self._save)
            else:
                return
            self.ui.customEditorPage.layout().addWidget(widget)

    def _icon_changed(self, doc: Document):
        if doc is self._current_doc:
            self.textEditor.setTitleIcon(IconRegistry.from_name(doc.icon, doc.icon_color))

    def _save(self):
        if not self._current_doc:
            return
        if self._current_doc.type in [DocumentType.DOCUMENT, DocumentType.STORY_STRUCTURE]:
            self._current_doc.content = self.textEditor.textEdit.toHtml()
        self.repo.update_doc(self.novel, self._current_doc)

    def _title_changed(self, title: str):
        if self._current_doc:
            if title and title != self._current_doc.title:
                self._current_doc.title = title
                # emit_column_changed_in_tree(self.model, 0, QModelIndex())
                self.ui.treeDocuments.updateDocument(self._current_doc)
                self.repo.update_novel(self.novel)
