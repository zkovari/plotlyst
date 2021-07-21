from src.main.python.plotlyst.core.domain import Character, StoryLine
from src.main.python.plotlyst.test.common import create_character, create_story_line
from src.main.python.plotlyst.view.main_window import MainWindow


def test_main_window_is_initialized(qtbot, window: MainWindow):
    assert window

    assert window.btnScenes.isChecked()
    assert window.scenes_outline_view.widget.isVisible()


def test_create_new_character(qtbot, window: MainWindow):
    create_character(qtbot, window, 'Tom')
    assert window.novel.characters == [Character(id=1, name='Tom')]


def test_create_story_line(qtbot, window: MainWindow):
    create_story_line(qtbot, window, 'MainStory')
    assert window.novel.story_lines == [StoryLine(id=1, text='MainStory')]
