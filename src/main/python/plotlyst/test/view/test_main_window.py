from PyQt5.QtWidgets import QApplication

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.test.conftest import get_main_window
from src.main.python.plotlyst.view.main_window import MainWindow


# def test_main_window_with_db_on_disk(qtbot, window_with_disk_db):
#     assert window_with_disk_db
#
#     assert window_with_disk_db.btnScenes.isChecked()
#     assert window_with_disk_db.scenes_outline_view.widget.isVisible()


def test_empty_window(qtbot, test_client):
    assert not client.novels()

    window = get_main_window(qtbot)

    assert window.btnHome.isVisible()
    assert window.btnHome.isChecked()
    assert not window.btnNovel.isVisible()
    assert not window.btnCharacters.isVisible()
    assert not window.btnScenes.isVisible()
    assert not window.btnReport.isVisible()
    assert not window.btnNotes.isVisible()
    assert not window.btnTimeline.isVisible()


def test_change_font_size(qtbot, window: MainWindow):
    font_size = QApplication.font().pointSize()
    window.actionIncreaseFontSize.trigger()
    window.actionIncreaseFontSize.trigger()
    assert QApplication.font().pointSize() == font_size + 2

    window.actionDecreaseFontSize.trigger()
    assert QApplication.font().pointSize() == font_size + 1
