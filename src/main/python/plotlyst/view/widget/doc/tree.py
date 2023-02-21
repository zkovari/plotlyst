import sys
from functools import partial
from typing import Set, Optional, Dict

from PyQt6.QtCore import pyqtSignal, Qt, QMimeData, QPointF
from PyQt6.QtWidgets import QMainWindow, QApplication
from qthandy import clear_layout, vspacer, retain_when_hidden, translucent, gc
from qthandy.filter import DragEventFilter, DropEventFilter

from src.main.python.plotlyst.core.domain import Document, Novel
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode


class DocumentWidget(ContainerNode):
    def __init__(self, doc: Document, parent=None):
        super(DocumentWidget, self).__init__(doc.title, parent)
        self._doc = doc

        retain_when_hidden(self._icon)
        self.refresh()

    def doc(self) -> Document:
        return self._doc

    def refresh(self):
        if self._doc.icon:
            self._icon.setIcon(IconRegistry.from_name(self._doc.icon, self._doc.icon_color))
            self._icon.setVisible(True)
        else:
            self._icon.setHidden(True)

        self._lblTitle.setText(self._doc.title)

    # @overrides
    # def eventFilter(self, watched: 'QObject', event: 'QEvent') -> bool:
    #     if event.type() == QEvent.Type.Enter:
    #         if not self._icon.isVisible():
    #             self._icon.setVisible(True)
    #     elif event.type() == QEvent.Type.Leave:
    #         if not self._doc.icon:
    #             self._icon.setHidden(True)
    #     return super().eventFilter(watched, event)


class DocumentsTreeView(TreeView):
    DOC_MIME_TYPE: str = 'application/document'
    documentSelected = pyqtSignal(Document)

    def __init__(self, parent=None):
        super(DocumentsTreeView, self).__init__(parent)
        self._novel: Optional[Novel] = None
        self._docs: Dict[Document, DocumentWidget] = {}
        self._selectedDocuments: Set[Document] = set()

        self._dummyWdg: Optional[DocumentWidget] = None
        self._toBeRemoved: Optional[DocumentWidget] = None

        self.setStyleSheet('DocumentsTreeView {background-color: rgb(244, 244, 244);}')

        self.repo = RepositoryPersistenceManager.instance()

    def setNovel(self, novel: Novel):
        self._novel = novel
        self.refresh()

    def refresh(self):
        self.clearSelection()
        self._docs.clear()
        clear_layout(self)

        for doc in self._novel.documents:
            wdg = self.__initDocWidget(doc)
            self._centralWidget.layout().addWidget(wdg)
            self._traverseChildren(doc, wdg)

        self._centralWidget.layout().addWidget(vspacer())

    def clearSelection(self):
        for doc in self._selectedDocuments:
            self._docs[doc].deselect()
        self._selectedDocuments.clear()

    def _traverseChildren(self, doc: Document, wdg: DocumentWidget):
        for child in doc.children:
            childWdg = self.__initDocWidget(child)
            wdg.addChild(childWdg)
            self._traverseChildren(child, childWdg)

    def _docSelectionChanged(self, wdg: DocumentWidget, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedDocuments.add(wdg.doc())
            self.documentSelected.emit(wdg.doc())
        elif wdg.doc() in self._selectedDocuments:
            self._selectedDocuments.remove(wdg.doc())

    def _dragStarted(self, wdg: DocumentWidget):
        wdg.setHidden(True)
        self._dummyWdg = DocumentWidget(wdg.doc())
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
        if self._dummyWdg.parent() is self._centralWidget:
            # ref = None
            # new_widget.setParent(self._centralWidget)
            i = self._centralWidget.layout().indexOf(self._dummyWdg)
            self._centralWidget.layout().insertWidget(i, new_widget)
        elif isinstance(self._dummyWdg.parent().parent(), DocumentWidget):
            doc_wdg: DocumentWidget = self._dummyWdg.parent().parent()
            # ref.chapter = chapter_wdg.chapter()
            # new_widget.setParent(doc_wdg)
            i = doc_wdg.containerWidget().layout().indexOf(self._dummyWdg)
            doc_wdg.insertChild(i, new_widget)

        self._dummyWdg.setHidden(True)
        # self.repo.update_novel(self._novel)

    def __initDocWidget(self, doc: Document) -> DocumentWidget:
        wdg = DocumentWidget(doc)
        wdg.selectionChanged.connect(partial(self._docSelectionChanged, wdg))
        # wdg.deleted.connect(partial(self._deleteChapterWidget, chapterWdg))
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


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)

            self.resize(500, 500)

            self.widget = DocumentsTreeView(self)
            novel = Novel('test')
            doc1 = Document('Doc 1')
            novel.documents.append(doc1)
            self.widget.setNovel(novel)
            self.setCentralWidget(self.widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
