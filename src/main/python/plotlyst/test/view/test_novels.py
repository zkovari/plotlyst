from src.main.python.plotlyst.test.common import create_story_line, go_to_novel, click_on_item, patch_confirmed
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.novel_view import NovelView


def test_create_story_line(qtbot, filled_window: MainWindow):
    create_story_line(qtbot, filled_window, 'New Storyline')

    assert filled_window.novel.story_lines
    assert filled_window.novel.story_lines[-1].text == 'New Storyline'


def test_delete_storyline(qtbot, filled_window: MainWindow, monkeypatch):
    view: NovelView = go_to_novel(filled_window)
    click_on_item(qtbot, view.ui.tblStoryLines, 0, 1)
    assert len(view.novel.story_lines) == 3
    storyline = view.novel.story_lines[0]
    assert storyline in view.novel.scenes[0].story_lines

    patch_confirmed(monkeypatch)
    view.ui.btnRemove.click()

    assert len(view.novel.story_lines) == 2
    assert storyline not in view.novel.story_lines
    assert not view.novel.scenes[0].story_lines
