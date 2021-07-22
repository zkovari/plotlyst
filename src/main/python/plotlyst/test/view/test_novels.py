from src.main.python.plotlyst.core.domain import StoryLine
from src.main.python.plotlyst.settings import STORY_LINE_COLOR_CODES
from src.main.python.plotlyst.test.common import create_story_line, go_to_novel, click_on_item, patch_confirmed
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.novel_view import NovelView


def test_create_story_line(qtbot, window: MainWindow):
    create_story_line(qtbot, window, 'MainStory')
    assert window.novel.story_lines == [StoryLine(id=1, text='MainStory', color_hexa=STORY_LINE_COLOR_CODES[0])]


def test_delete_storyline(qtbot, filled_window: MainWindow, monkeypatch):
    view: NovelView = go_to_novel(filled_window)

    click_on_item(qtbot, view.ui.tblStoryLines, 0, 0)
    assert len(view.novel.story_lines) == 3
    storyline = view.novel.story_lines[0]
    assert storyline in view.novel.scenes[0].story_lines

    patch_confirmed(monkeypatch)
    view.ui.btnRemove.click()

    assert len(view.novel.story_lines) == 2
    assert storyline not in view.novel.story_lines
    assert not view.novel.scenes[0].story_lines
