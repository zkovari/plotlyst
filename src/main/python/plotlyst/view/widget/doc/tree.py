import sys
from typing import Set, Optional, Dict

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QApplication
from qthandy import clear_layout, vspacer, retain_when_hidden

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
            wdg = DocumentWidget(doc)
            self._centralWidget.layout().addWidget(wdg)
            self._traverseChildren(doc, wdg)

        self._centralWidget.layout().addWidget(vspacer())

    def clearSelection(self):
        for doc in self._selectedDocuments:
            self._docs[doc].deselect()
        self._selectedDocuments.clear()

    def _traverseChildren(self, doc: Document, wdg: DocumentWidget):
        for child in doc.children:
            childWdg = DocumentWidget(child)
            wdg.addChild(childWdg)
            self._traverseChildren(child, childWdg)


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
