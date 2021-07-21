from src.main.python.plotlyst.model.scenes_model import ScenesNotesTableModel
from src.main.python.plotlyst.test.common import go_to_notes, assert_data
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.notes_view import NotesView


def test_notes_display(qtbot, filled_window: MainWindow):
    view: NotesView = go_to_notes(filled_window)

    assert view.ui.lstScenes.isVisible()
    assert_data(view.scenes_model, 'Scene 1', 0, ScenesNotesTableModel.ColTitle)
    assert_data(view.scenes_model, 'Scene 2', 1, ScenesNotesTableModel.ColTitle)
