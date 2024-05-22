"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
import os
from typing import Optional

import qtanim
from PyQt6.QtGui import QFont
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from overrides import overrides
from qthandy import clear_layout, margins, bold, italic
from qttextedit.ops import TextEditorSettingsSection, FontSectionSettingWidget

from plotlyst.core.client import json_client
from plotlyst.core.domain import Novel, Document, DocumentType, FontSettings
from plotlyst.env import app_env
from plotlyst.events import SceneChangedEvent, SceneDeletedEvent
from plotlyst.service.cache import characters_registry
from plotlyst.view._view import AbstractNovelView
from plotlyst.view.common import ButtonPressResizeEventFilter
from plotlyst.view.generated.notes_view_ui import Ui_NotesView
from plotlyst.view.icons import IconRegistry, avatars
from plotlyst.view.widget.doc.browser import DocumentAdditionMenu
from plotlyst.view.widget.doc.premise import PremiseBuilderWidget
from plotlyst.view.widget.input import DocumentTextEditor
from plotlyst.view.widget.tree import TreeSettings


class DocumentsView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel, [SceneChangedEvent, SceneDeletedEvent])
        self.ui = Ui_NotesView()
        self.ui.setupUi(self.widget)
        self._current_doc: Optional[Document] = None

        self.ui.btnDocuments.setIcon(IconRegistry.document_edition_icon())
        bold(self.ui.lblTitle)

        italic(self.ui.lblMissingFile)
        self.ui.btnMissingFile.setIcon(IconRegistry.from_name('mdi6.file-alert-outline'))
        bold(self.ui.lblMissingFileReference)
        italic(self.ui.lblMissingFileReference)

        self.ui.btnTreeToggle.setIcon(IconRegistry.from_name('mdi.file-tree-outline'))
        self.ui.btnTreeToggleSecondary.setIcon(IconRegistry.from_name('mdi.file-tree-outline'))
        self.ui.btnTreeToggleSecondary.setHidden(True)
        self.ui.btnTreeToggle.clicked.connect(self._hide_sidebar)
        self.ui.btnTreeToggleSecondary.clicked.connect(self._show_sidebar)

        self.ui.splitter.setSizes([150, 500])

        self.ui.treeDocuments.setSettings(TreeSettings(font_incr=2))
        self.ui.treeDocuments.setNovel(self.novel)
        self.ui.treeDocuments.documentSelected.connect(self._edit)
        self.ui.treeDocuments.documentDeleted.connect(self._clear_text_editor)
        self.ui.treeDocuments.documentIconChanged.connect(self._icon_changed)
        self.ui.treeDocuments.documentTitleChanged.connect(self._title_changed)

        self.textEditor: Optional[DocumentTextEditor] = None
        self.pdfEditor = QPdfView(self.ui.pdfPage)
        self.pdfDoc = QPdfDocument(self.pdfEditor)
        self.pdfEditor.setDocument(self.pdfDoc)
        self.ui.pdfPage.layout().addWidget(self.pdfEditor)

        self.ui.btnAdd.setIcon(IconRegistry.plus_icon('white'))
        self.ui.btnAdd.installEventFilter(ButtonPressResizeEventFilter(self.ui.btnAdd))
        menu = DocumentAdditionMenu(self.novel, self.ui.btnAdd)
        menu.documentTriggered.connect(self._add_doc)

        self.ui.stackedEditor.setCurrentWidget(self.ui.emptyPage)

    @overrides
    def refresh(self):
        self.ui.treeDocuments.refresh()

    def _add_doc(self, doc: Document):
        self.ui.treeDocuments.addDocument(doc)

    def _init_text_editor(self):
        def settings_ready():
            section: FontSectionSettingWidget = self.textEditor.settingsWidget().section(TextEditorSettingsSection.FONT)
            section.fontSelected.connect(self._fontChanged)

        self._clear_text_editor()

        self.textEditor = DocumentTextEditor(self.ui.docEditorPage)
        margins(self.textEditor, top=50, right=10)
        self.ui.docEditorPage.layout().addWidget(self.textEditor)

        if self.novel.prefs.docs.font.get(app_env.platform(), ''):
            font_: QFont = self.textEditor.textEdit.font()
            font_.setFamily(self.novel.prefs.docs.font[app_env.platform()].family)
            self.textEditor.textEdit.setFont(font_)
            self.textEditor.textTitle.setPlaceholderText('Untitled')
        self.textEditor.textEdit.textChanged.connect(self._save)
        self.textEditor.titleChanged.connect(self._title_changed_in_editor)
        self.textEditor.iconChanged.connect(self._icon_changed_in_editor)
        self.textEditor.settingsAttached.connect(settings_ready)

    def _clear_text_editor(self):
        self.pdfDoc.close()
        clear_layout(self.ui.docEditorPage.layout())
        self.ui.stackedEditor.setCurrentWidget(self.ui.emptyPage)

    def _edit(self, doc: Document):
        self._current_doc = doc

        if self._current_doc.type in [DocumentType.DOCUMENT, DocumentType.STORY_STRUCTURE]:
            self._edit_document()
        else:
            # self.ui.stackedEditor.setCurrentWidget(self.ui.customEditorPage)
            # clear_layout(self.ui.customEditorPage)
            # if self._current_doc.type == DocumentType.MICE:
            #     widget = MiceQuotientDoc(self._current_doc, self._current_doc.data)
            #     widget.changed.connect(self._save)
            if self._current_doc.type == DocumentType.PDF:
                self._edit_pdf()
            elif self._current_doc.type == DocumentType.PREMISE:
                self._edit_premise()

    def _edit_document(self):
        self._init_text_editor()
        if not self._current_doc.loaded:
            json_client.load_document(self.novel, self._current_doc)
        self.ui.stackedEditor.setCurrentWidget(self.ui.docEditorPage)
        self.textEditor.setGrammarCheckEnabled(False)

        char = characters_registry.character(str(self._current_doc.character_id))
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
            self.textEditor.asyncCheckGrammar()

    def _edit_pdf(self):
        self.pdfDoc.close()
        if os.path.exists(self._current_doc.file):
            self.pdfDoc.load(self._current_doc.file)
            self.ui.stackedEditor.setCurrentWidget(self.ui.pdfPage)
        else:
            self.ui.lblMissingFileReference.setText(self._current_doc.file)
            self.ui.stackedEditor.setCurrentWidget(self.ui.missingFilePage)

    def _edit_premise(self):
        clear_layout(self.ui.customEditorPage)

        wdg = PremiseBuilderWidget(self._current_doc)
        self.ui.customEditorPage.layout().addWidget(wdg)

        self.ui.stackedEditor.setCurrentWidget(self.ui.customEditorPage)

    def _icon_changed(self, doc: Document):
        if doc is self._current_doc:
            self.textEditor.setTitleIcon(IconRegistry.from_name(doc.icon, doc.icon_color))

    def _icon_changed_in_editor(self, name: str, color: str):
        if self._current_doc:
            self._current_doc.icon = name
            self._current_doc.icon_color = color
            self.ui.treeDocuments.updateDocument(self._current_doc)
            self.repo.update_novel(self.novel)

    def _save(self):
        if not self._current_doc:
            return
        if self._current_doc.type in [DocumentType.DOCUMENT, DocumentType.STORY_STRUCTURE]:
            self._current_doc.content = self.textEditor.textEdit.toHtml()
        self.repo.update_doc(self.novel, self._current_doc)

    def _title_changed(self, doc: Document):
        if doc is self._current_doc:
            self.textEditor.setTitle(doc.title)

    def _title_changed_in_editor(self, title: str):
        if self._current_doc:
            if title and title != self._current_doc.title:
                self._current_doc.title = title
                self.ui.treeDocuments.updateDocument(self._current_doc)
                self.repo.update_novel(self.novel)

    def _fontChanged(self, family: str):
        if app_env.platform() not in self.novel.prefs.docs.font.keys():
            self.novel.prefs.docs.font[app_env.platform()] = FontSettings()
        fontSettings = self.novel.prefs.docs.font[app_env.platform()]
        fontSettings.family = family
        self.repo.update_novel(self.novel)

    def _hide_sidebar(self):
        qtanim.toggle_expansion(self.ui.wdgDocs, False, teardown=lambda: qtanim.fade_in(self.ui.btnTreeToggleSecondary))
        self.ui.btnTreeToggleSecondary.setChecked(False)

    def _show_sidebar(self):
        qtanim.toggle_expansion(self.ui.wdgDocs, True)
        self.ui.btnTreeToggle.setChecked(True)
        self.ui.btnTreeToggleSecondary.setVisible(False)
