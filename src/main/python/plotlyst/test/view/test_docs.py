from PyQt5.QtCore import QModelIndex

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.test.common import go_to_docs, click_on_item
from src.main.python.plotlyst.view.docs_view import DocumentsView
from src.main.python.plotlyst.view.main_window import MainWindow


def test_notes_display(qtbot, filled_window: MainWindow):
    view: DocumentsView = go_to_docs(filled_window)

    click_on_item(qtbot, view.ui.treeDocuments, 0, 0, QModelIndex())
    qtbot.keyClicks(view.ui.editor.textEditor, 'Test content')

    json_client.load_document(view.novel, view.novel.documents[0])
    assert 'Test content' in view.novel.documents[0].content
