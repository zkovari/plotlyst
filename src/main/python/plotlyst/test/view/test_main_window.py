from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.test.common import go_to_home, create_novel
from src.main.python.plotlyst.test.conftest import get_main_window
from src.main.python.plotlyst.view.home_view import HomeView
from src.main.python.plotlyst.view.main_window import MainWindow


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


def test_load_new_empty_novel(qtbot, filled_window: MainWindow):
    view: HomeView = go_to_home(filled_window)
    assert len(view.novel_cards) == 1

    new_title = 'New title'
    create_novel(filled_window, new_title)
    assert len(view.novel_cards) == 2

    card = view.novel_cards[1]
    assert card.novel.id
    assert card.novel.title == new_title
    qtbot.mouseClick(card, Qt.LeftButton)

    card.btnLoad.click()

    assert filled_window.btnNovel.isEnabled()
    assert filled_window.btnNovel.isVisible()
    assert filled_window.btnCharacters.isVisible()
    assert filled_window.btnCharacters.isEnabled()
    assert filled_window.btnScenes.isVisible()
    assert not filled_window.btnScenes.isEnabled()
    assert filled_window.btnReport.isVisible()
    assert not filled_window.btnReport.isEnabled()
    assert filled_window.btnNotes.isVisible()
    assert not filled_window.btnNotes.isEnabled()
    assert filled_window.btnTimeline.isVisible()
    assert not filled_window.btnTimeline.isEnabled()

    first_card = view.novel_cards[0]
    assert first_card.novel.id
    qtbot.mouseClick(first_card, Qt.LeftButton)

    first_card.btnLoad.click()
    assert filled_window.btnNovel.isEnabled()
    assert filled_window.btnNovel.isVisible()
    assert filled_window.btnCharacters.isVisible()
    assert filled_window.btnCharacters.isEnabled()
    assert filled_window.btnScenes.isVisible()
    assert filled_window.btnScenes.isEnabled()
    assert filled_window.btnReport.isVisible()
    assert filled_window.btnReport.isEnabled()
    assert filled_window.btnNotes.isVisible()
    assert filled_window.btnNotes.isEnabled()
    assert filled_window.btnTimeline.isVisible()
    assert filled_window.btnTimeline.isEnabled()
