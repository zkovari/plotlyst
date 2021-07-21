from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QDialog, QApplication

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.test.common import go_to_home
from src.main.python.plotlyst.view.dialog.new_novel import NovelEditionDialog
from src.main.python.plotlyst.view.home_view import HomeView
from src.main.python.plotlyst.view.main_window import MainWindow


# def test_novel_deletion(qtbot, filled_window: MainWindow, monkeypatch):
#     view: HomeView = go_to_home(filled_window)
#
#     assert len(view.novel_cards) == 1
#     card = view.novel_cards[0]
#     qtbot.mouseClick(card, Qt.LeftButton)
#
#     patch_confirmed(monkeypatch)
#     view.ui.btnDelete.click()
#

def edit_novel(new_title: str):
    dialog: QDialog = QApplication.instance().activeModalWidget()
    try:
        assert isinstance(dialog, NovelEditionDialog)
        edition_dialog: NovelEditionDialog = dialog
        edition_dialog.lineTitle.setText(new_title)
        edition_dialog.btnConfirm.click()
    finally:
        dialog.close()


def test_novel_edition(qtbot, filled_window: MainWindow, monkeypatch):
    view: HomeView = go_to_home(filled_window)

    assert len(view.novel_cards) == 1
    card = view.novel_cards[0]
    qtbot.mouseClick(card, Qt.LeftButton)
    new_title = 'New title'
    QTimer.singleShot(40, lambda: edit_novel(new_title))
    view.ui.btnEdit.click()

    assert card.label.text() == new_title
    assert client.fetch_novel(1).title == new_title
