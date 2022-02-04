from uuid import UUID

from PyQt5.QtCore import Qt, QTimer

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.test.common import go_to_home, patch_confirmed, create_novel, go_to_novel, \
    edit_novel_dialog, import_from_scrivener
from src.main.python.plotlyst.test.view.test_main_window import assert_views
from src.main.python.plotlyst.view.home_view import HomeView
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.novel_view import NovelView


def test_delete_novel(qtbot, filled_window: MainWindow, monkeypatch):
    view: HomeView = go_to_home(filled_window)

    assert len(view.novel_cards) == 1
    card = view.novel_cards[0]
    qtbot.mouseClick(card, Qt.LeftButton)

    patch_confirmed(monkeypatch)
    view.ui.btnDelete.click()

    assert len(view.novel_cards) == 0


def test_edit_novel(qtbot, filled_window: MainWindow):
    view: HomeView = go_to_home(filled_window)

    assert len(view.novel_cards) == 1
    card = view.novel_cards[0]
    qtbot.mouseClick(card, Qt.LeftButton)
    new_title = 'New title'
    QTimer.singleShot(40, lambda: edit_novel_dialog(new_title))
    view.ui.btnEdit.click()

    assert card.textName.toPlainText() == new_title
    assert client.novels()[0].title == new_title

    novel_view: NovelView = go_to_novel(filled_window)
    assert novel_view.ui.lblTitle.text() == new_title


def test_create_new_novel(qtbot, filled_window: MainWindow):
    view: HomeView = go_to_home(filled_window)
    assert len(view.novel_cards) == 1

    new_title = 'New title'
    create_novel(filled_window, new_title)

    assert len(view.novel_cards) == 2

    novels = client.novels()
    assert len(novels) == 2
    assert novels[1].id
    assert novels[1].title == new_title


def test_import_from_scrivener(qtbot, window: MainWindow, monkeypatch):
    # folder = Path(sys.path[0]).joinpath('resources/scrivener/v3/NovelWithParts')
    # monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: folder)

    view: HomeView = go_to_home(window)
    assert len(view.novel_cards) == 0

    import_from_scrivener(window, monkeypatch)

    assert len(view.novel_cards) == 1

    card = view.novel_cards[0]
    assert card.novel.title == 'Importer project'
    assert card.novel.id == UUID('C4B3D990-B9C2-4FE6-861E-B06B498283A4')
    qtbot.mouseClick(card, Qt.LeftButton)

    view.ui.btnActivate.click()
    assert_views(window)
