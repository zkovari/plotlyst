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
from functools import partial
from typing import Set, Optional, Dict

from PyQt6.QtCore import pyqtSignal, Qt, QMimeData, QPointF, QModelIndex
from PyQt6.QtWidgets import QListView
from overrides import overrides
from qthandy import clear_layout, vspacer, translucent, gc, ask_confirmation, pointy, retain_when_hidden
from qthandy.filter import DragEventFilter, DropEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import recursive
from src.main.python.plotlyst.core.domain import Document, Novel, DocumentType, Character
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.model.characters_model import CharactersTableModel
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import fade_out_and_gc, action
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode, TreeSettings


class DocumentAdditionMenu(MenuWidget):
    documentTriggered = pyqtSignal(Document)

    def __init__(self, novel: Novel, parent=None):
        super(DocumentAdditionMenu, self).__init__(parent)
        self._novel = novel

        self.addAction(action('Document', IconRegistry.document_edition_icon(), lambda: self._documentSelected()))

        self._character_menu = MenuWidget()
        self._character_menu.setTitle('Link characters')
        self._character_menu.setIcon(IconRegistry.character_icon())
        _view = QListView()
        pointy(_view)
        _view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        _view.clicked.connect(self._characterSelected)
        _view.setModel(CharactersTableModel(self._novel))
        self._character_menu.addWidget(_view)
        self.addMenu(self._character_menu)

    def _characterSelected(self, char_index: QModelIndex):
        char = char_index.data(CharactersTableModel.CharacterRole)
        self._documentSelected(character=char)
        self._character_menu.close()

    def _documentSelected(self, docType=DocumentType.DOCUMENT, character: Optional[Character] = None):
        doc = Document('New Document', type=docType)
        if character:
            doc.title = ''
            doc.character_id = character.id
        doc.loaded = True

        self.documentTriggered.emit(doc)


class DocumentWidget(ContainerNode):
    added = pyqtSignal(Document)

    def __init__(self, novel: Novel, doc: Document, parent=None, settings: Optional[TreeSettings] = None):
        super(DocumentWidget, self).__init__(doc.title, parent, settings=settings)
        self._novel = novel
        self._doc = doc

        retain_when_hidden(self._icon)

        self._actionChangeIcon.setVisible(True)
        menu = DocumentAdditionMenu(self._novel, self._btnAdd)
        menu.documentTriggered.connect(self.added.emit)
        self.refresh()

    def doc(self) -> Document:
        return self._doc

    def refresh(self):
        self._lblTitle.setText(self._doc.title)

        if self._doc.icon:
            self._icon.setIcon(IconRegistry.from_name(self._doc.icon, self._doc.icon_color))
            self._icon.setVisible(True)
        elif self._doc.character_id:
            char = self._doc.character(app_env.novel)
            self._lblTitle.setText(char.name)
            self._icon.setIcon(avatars.avatar(char))
            self._icon.setVisible(True)
        else:
            self._icon.setHidden(True)

    @overrides
    def _iconChanged(self, iconName: str, iconColor: str):
        self._doc.icon = iconName
        self._doc.icon_color = iconColor


class DocumentsTreeView(TreeView):
    DOC_MIME_TYPE: str = 'application/document'
    documentSelected = pyqtSignal(Document)
    documentDeleted = pyqtSignal(Document)
    documentIconChanged = pyqtSignal(Document)

    def __init__(self, parent=None, settings: Optional[TreeSettings] = None):
        super(DocumentsTreeView, self).__init__(parent)
        self._novel: Optional[Novel] = None
        self._settings = settings
        self._docs: Dict[Document, DocumentWidget] = {}
        self._selectedDocuments: Set[Document] = set()

        self._dummyWdg: Optional[DocumentWidget] = None
        self._toBeRemoved: Optional[DocumentWidget] = None

        self._centralWidget.setProperty('bg', True)

        self.repo = RepositoryPersistenceManager.instance()

    def setSettings(self, settings: TreeSettings):
        self._settings = settings

    def setNovel(self, novel: Novel):
        self._novel = novel

        self.refresh()

    def addDocument(self, doc: Document):
        self._novel.documents.append(doc)
        wdg = self.__initDocWidget(doc)
        self._centralWidget.layout().insertWidget(self._centralWidget.layout().count() - 1, wdg)

        self._save()

    def refresh(self):
        def addChildWdg(parent: Document, child: Document):
            childWdg = self.__initDocWidget(child)
            self._docs[parent].addChild(childWdg)

        self.clearSelection()
        self._docs.clear()
        clear_layout(self._centralWidget)

        for doc in self._novel.documents:
            wdg = self.__initDocWidget(doc)
            self._centralWidget.layout().addWidget(wdg)
            recursive(doc, lambda parent: parent.children, addChildWdg)

        self._centralWidget.layout().addWidget(vspacer())

    def updateDocument(self, doc: Document):
        self._docs[doc].refresh()

    def clearSelection(self):
        for doc in self._selectedDocuments:
            self._docs[doc].deselect()
        self._selectedDocuments.clear()

    def _docSelectionChanged(self, wdg: DocumentWidget, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedDocuments.add(wdg.doc())
            self.documentSelected.emit(wdg.doc())
        elif wdg.doc() in self._selectedDocuments:
            self._selectedDocuments.remove(wdg.doc())

    def _dragStarted(self, wdg: DocumentWidget):
        wdg.setHidden(True)
        self._dummyWdg = DocumentWidget(self._novel, wdg.doc(), settings=self._settings)
        self._dummyWdg.setPlusButtonEnabled(False)
        self._dummyWdg.setMenuEnabled(False)
        translucent(self._dummyWdg)
        self._dummyWdg.setHidden(True)
        self._dummyWdg.setParent(self._centralWidget)
        self._dummyWdg.setAcceptDrops(True)
        self._dummyWdg.installEventFilter(
            DropEventFilter(self._dummyWdg, [self.DOC_MIME_TYPE], droppedSlot=self._drop))

    def _dragStopped(self, wdg: DocumentWidget):
        if self._dummyWdg:
            gc(self._dummyWdg)
            self._dummyWdg = None

        if self._toBeRemoved:
            gc(self._toBeRemoved)
            self._toBeRemoved = None
        else:
            wdg.setVisible(True)

    def _dragMovedOnDoc(self, wdg: DocumentWidget, edge: Qt.Edge, point: QPointF):
        i = wdg.parent().layout().indexOf(wdg)
        if edge == Qt.Edge.TopEdge:
            wdg.parent().layout().insertWidget(i, self._dummyWdg)
        elif point.x() > 50:
            wdg.insertChild(0, self._dummyWdg)
        else:
            wdg.parent().layout().insertWidget(i + 1, self._dummyWdg)

        self._dummyWdg.setVisible(True)

    def _drop(self, mimeData: QMimeData):
        self.clearSelection()

        if self._dummyWdg.isHidden():
            return
        ref: Document = mimeData.reference()
        self._toBeRemoved = self._docs[ref]
        new_widget = self.__initDocWidget(ref)
        for child in self._toBeRemoved.childrenWidgets():
            new_widget.addChild(child)

        if self._dummyWdg.parent() is self._centralWidget:
            new_index = self._centralWidget.layout().indexOf(self._dummyWdg)
            if self._toBeRemoved.parent() is self._centralWidget:  # swap order on top
                old_index = self._centralWidget.layout().indexOf(self._toBeRemoved)
                self._novel.documents.remove(ref)
                if old_index < new_index:
                    self._novel.documents.insert(new_index - 1, ref)
                else:
                    self._novel.documents.insert(new_index, ref)
            else:
                self._removeFromParentDoc(ref, self._toBeRemoved)
                self._novel.documents.insert(new_index, ref)

            self._centralWidget.layout().insertWidget(new_index, new_widget)
        elif isinstance(self._dummyWdg.parent().parent(), DocumentWidget):
            doc_parent_wdg: DocumentWidget = self._dummyWdg.parent().parent()
            new_index = doc_parent_wdg.containerWidget().layout().indexOf(self._dummyWdg)
            if self._toBeRemoved.parent() is not self._centralWidget and \
                    self._toBeRemoved.parent().parent() is self._dummyWdg.parent().parent():  # swap under same parent doc
                old_index = doc_parent_wdg.layout().indexOf(self._toBeRemoved)
                doc_parent_wdg.doc().children.remove(ref)
                if old_index < new_index:
                    doc_parent_wdg.insertChild(new_index - 1, new_widget)
                else:
                    doc_parent_wdg.doc().children.insert(new_index, ref)
            else:
                self._removeFromParentDoc(ref, self._toBeRemoved)
                doc_parent_wdg.doc().children.insert(new_index, ref)

            doc_parent_wdg.insertChild(new_index, new_widget)

        self._dummyWdg.setHidden(True)
        self._save()

    def _addDoc(self, wdg: DocumentWidget, newDoc: Document):
        newWdg = self.__initDocWidget(newDoc)
        wdg.addChild(newWdg)
        wdg.doc().children.append(newDoc)
        self._save()

    def _deleteDocWidget(self, wdg: DocumentWidget):
        doc = wdg.doc()
        if not ask_confirmation(f"Delete document '{doc.title}'?", self._centralWidget):
            return
        if doc in self._selectedDocuments:
            self._selectedDocuments.remove(doc)
        self._docs.pop(doc)

        fade_out_and_gc(wdg.parent(), wdg)

        self.repo.delete_doc(self._novel, doc)
        self.documentDeleted.emit(doc)

        self._removeFromParentDoc(doc, wdg)
        self._save()

    def _removeFromParentDoc(self, doc: Document, wdg: DocumentWidget):
        if wdg.parent() is self._centralWidget:
            self._novel.documents.remove(doc)
        else:
            parent: DocumentWidget = wdg.parent().parent()
            parent.doc().children.remove(doc)

    def _save(self):
        self.repo.update_novel(self._novel)

    def _iconChanged(self, doc: Document):
        self._save()
        self.documentIconChanged.emit(doc)

    def __initDocWidget(self, doc: Document) -> DocumentWidget:
        wdg = DocumentWidget(self._novel, doc, settings=self._settings)
        wdg.selectionChanged.connect(partial(self._docSelectionChanged, wdg))
        wdg.deleted.connect(partial(self._deleteDocWidget, wdg))
        wdg.added.connect(partial(self._addDoc, wdg))
        wdg.iconChanged.connect(partial(self._iconChanged, doc))
        wdg.installEventFilter(
            DragEventFilter(wdg, self.DOC_MIME_TYPE, dataFunc=lambda wdg: wdg.doc(),
                            grabbed=wdg.titleLabel(),
                            startedSlot=partial(self._dragStarted, wdg),
                            finishedSlot=partial(self._dragStopped, wdg)))
        wdg.titleWidget().setAcceptDrops(True)
        wdg.titleWidget().installEventFilter(
            DropEventFilter(wdg, [self.DOC_MIME_TYPE, self.DOC_MIME_TYPE],
                            motionDetection=Qt.Orientation.Vertical,
                            motionSlot=partial(self._dragMovedOnDoc, wdg),
                            droppedSlot=self._drop
                            )
        )

        self._docs[doc] = wdg

        return wdg
