from src.main.python.plotlyst.model.scenes_model import ScenesNotesTableModel
from src.main.python.plotlyst.test.common import go_to_timeline, assert_data
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.timeline_view import TimelineView


def test_timeline_display(qtbot, filled_window: MainWindow):
    view: TimelineView = go_to_timeline(filled_window)

    assert view.ui.tblScenes.isVisible()
    assert_data(view.model, 'Scene 1', 0, ScenesNotesTableModel.ColTitle)
    assert_data(view.model, 'Scene 2', 1, ScenesNotesTableModel.ColTitle)

    assert_data(view.model, 0, 0, ScenesNotesTableModel.ColTime)
    assert_data(view.model, 0, 0, ScenesNotesTableModel.ColTime)
