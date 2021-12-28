from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.test.common import create_character, go_to_characters, click_on_item, patch_confirmed, \
    go_to_scenes
from src.main.python.plotlyst.view.characters_view import CharactersView
from src.main.python.plotlyst.view.main_window import MainWindow


def test_create_character(qtbot, filled_window: MainWindow):
    create_character(qtbot, filled_window, 'Tom')
    assert filled_window.novel.characters
    assert filled_window.novel.characters[-1].name == 'Tom'
    assert filled_window.novel.characters[-1].id

    saved_novel = client.fetch_novel(filled_window.novel.id)
    assert len(saved_novel.characters) == len(filled_window.novel.characters)
    assert saved_novel.characters[-1].name == 'Tom'
    assert saved_novel.characters[-1].id


def test_edit_character(qtbot, filled_window: MainWindow):
    view: CharactersView = go_to_characters(filled_window)

    view.ui.btnTableView.click()

    assert not view.ui.btnEdit.isEnabled()
    assert not view.ui.btnDelete.isEnabled()
    click_on_item(qtbot, view.ui.tblCharacters, 0)
    assert view.ui.btnEdit.isEnabled()
    assert view.ui.btnDelete.isEnabled()

    view.ui.btnEdit.click()
    assert view.editor

    name = 'New name'
    view.editor.profile.setName(name)
    view.editor.ui.btnClose.click()

    assert view.novel.characters[0].name == name

    saved_novel = client.fetch_novel(filled_window.novel.id)
    assert saved_novel.characters[0].name == name


def test_delete_character(qtbot, filled_window: MainWindow, monkeypatch):
    view: CharactersView = go_to_characters(filled_window)

    view.ui.btnTableView.click()

    click_on_item(qtbot, view.ui.tblCharacters, 0)

    alfred = view.novel.characters[0]
    assert view.novel.scenes[0].pov == alfred
    assert alfred in view.novel.scenes[1].characters
    assert len(view.novel.characters) == 5
    assert view.model.rowCount() == 5
    patch_confirmed(monkeypatch)
    view.ui.btnDelete.click()

    assert len(view.novel.characters) == 4
    assert view.model.rowCount() == 4
    assert alfred not in view.novel.characters

    scenes_view = go_to_scenes(filled_window)
    assert not scenes_view.novel.scenes[0].pov
    assert alfred not in scenes_view.novel.scenes[1].characters

    saved_novel = client.fetch_novel(filled_window.novel.id)
    assert len(saved_novel.characters) == 4
    assert alfred not in saved_novel.characters
