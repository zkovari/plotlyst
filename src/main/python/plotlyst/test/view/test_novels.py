from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import default_story_structures
from src.main.python.plotlyst.test.common import create_dramatic_question, go_to_novel, click_on_item, \
    patch_confirmed, go_to_scenes
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.novel_view import NovelView


def test_create_dramatic_question(qtbot, filled_window: MainWindow):
    create_dramatic_question(qtbot, filled_window, 'New Storyline')

    assert filled_window.novel.dramatic_questions
    assert filled_window.novel.dramatic_questions[-1].text == 'New Storyline'


def test_delete_dramatic_question(qtbot, filled_window: MainWindow, monkeypatch):
    view: NovelView = go_to_novel(filled_window)
    click_on_item(qtbot, view.ui.tblDramaticQuestions, 0, 1)
    assert len(view.novel.dramatic_questions) == 3
    dq = view.novel.dramatic_questions[0]
    assert dq in view.novel.scenes[0].dramatic_questions

    patch_confirmed(monkeypatch)
    view.ui.btnRemove.click()

    assert len(view.novel.dramatic_questions) == 2
    assert dq not in view.novel.dramatic_questions
    assert not view.novel.scenes[0].dramatic_questions


def test_change_structure(qtbot, filled_window: MainWindow, monkeypatch):
    view: NovelView = go_to_novel(filled_window)
    view.novel.scenes[0].beat = view.novel.story_structure.beats[0]

    assert view.ui.cbStoryStructure.currentText() == 'Three Act Structure'

    patch_confirmed(monkeypatch)
    view.ui.cbStoryStructure.setCurrentIndex(1)

    assert view.ui.cbStoryStructure.currentText() == 'Save the Cat'
    assert view.novel.story_structure == default_story_structures[1]

    for scene in view.novel.scenes:
        assert scene.beat is None

    go_to_scenes(filled_window)

    persisted_novel = client.fetch_novel(view.novel.id)
    assert persisted_novel.story_structure == view.novel.story_structure


def test_structure_info(qtbot, filled_window: MainWindow):
    view: NovelView = go_to_novel(filled_window)

    assert not view.ui.btnStoryStructureInfo.isChecked()
    view.ui.btnStoryStructureInfo.click()
    assert view.ui.textStoryStructureInfo.isVisible()

    view.ui.btnStoryStructureInfo.click()
    assert not view.ui.textStoryStructureInfo.height()
