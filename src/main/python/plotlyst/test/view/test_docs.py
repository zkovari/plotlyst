from src.main.python.plotlyst.test.common import go_to_docs
from src.main.python.plotlyst.view.docs_view import DocumentsView
from src.main.python.plotlyst.view.main_window import MainWindow


def test_notes_display(qtbot, filled_window: MainWindow):
    view: DocumentsView = go_to_docs(filled_window)
