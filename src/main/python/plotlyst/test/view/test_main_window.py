from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Character, StoryLine
from src.main.python.plotlyst.test.common import create_character, create_story_line
from src.main.python.plotlyst.test.conftest import get_main_window
from src.main.python.plotlyst.view.main_window import MainWindow


def test_main_window(qtbot, window: MainWindow):
    assert window

    assert window.btnScenes.isChecked()
    assert window.scenes_outline_view.widget.isVisible()


def test_main_window_with_db_on_disk(qtbot, window_with_disk_db):
    assert window_with_disk_db

    assert window_with_disk_db.btnScenes.isChecked()
    assert window_with_disk_db.scenes_outline_view.widget.isVisible()


def test_empty_window(qtbot, test_client):
    assert len(client.novels()) == 1
    client.delete_novel(client.novels()[0])
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


def test_create_new_character(qtbot, window: MainWindow):
    create_character(qtbot, window, 'Tom')
    assert window.novel.characters == [Character(id=1, name='Tom')]


def test_create_story_line(qtbot, window: MainWindow):
    create_story_line(qtbot, window, 'MainStory')
    assert window.novel.story_lines == [StoryLine(id=1, text='MainStory')]
