from plotlyst.core.domain import Character, Scene, StoryLine
from plotlyst.test.common import assert_data, create_character, start_new_scene_editor, create_story_line
from plotlyst.view.main_window import MainWindow
from plotlyst.view.scenes_view import ScenesOutlineView


def test_main_window_is_initialized(qtbot, window: MainWindow):
    assert window

    assert window.tabWidget.currentWidget() == window.scenes_tab


def test_create_new_character(qtbot, window: MainWindow):
    create_character(qtbot, window, 'Tom')
    assert window.novel.characters == [Character(id=1, name='Tom')]


def test_create_new_scene(qtbot, window: MainWindow):
    scenes: ScenesOutlineView = start_new_scene_editor(window)

    qtbot.keyClicks(scenes.editor.ui.lineTitle, 'Scene 1')
    scenes.editor.ui.sbDay.setValue(1)

    scenes.editor.ui.btnClose.click()

    assert_data(scenes.ui.tblScenes.model(), 'Scene 1', 0, 1)
    assert window.novel.scenes == [Scene(id=1, title='Scene 1', type='action', day=1)]


def test_scene_characters(qtbot, window: MainWindow):
    create_character(qtbot, window, 'Tom')
    create_character(qtbot, window, 'Bob')

    scenes: ScenesOutlineView = start_new_scene_editor(window)
    qtbot.keyClicks(scenes.editor.ui.lineTitle, 'Scene 1')
    scenes.editor.ui.cbPov.setCurrentText('Tom')
    scenes.editor.ui.btnClose.click()

    scenes: ScenesOutlineView = start_new_scene_editor(window)
    qtbot.keyClicks(scenes.editor.ui.lineTitle, 'Scene 2')
    scenes.editor.ui.cbPov.setCurrentText('Bob')
    scenes.editor.ui.btnClose.click()


def test_create_story_line(qtbot, window: MainWindow):
    create_story_line(qtbot, window, 'MainStory')
    assert window.novel.story_lines == [StoryLine(id=1, text='MainStory')]
