from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import default_story_structures
from src.main.python.plotlyst.model.common import SelectionItemsModel
from src.main.python.plotlyst.test.common import create_plot, go_to_novel, click_on_item, \
    patch_confirmed, go_to_scenes
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.novel_view import NovelView


def test_create_plot(qtbot, filled_window: MainWindow):
    view: NovelView = go_to_novel(filled_window)
    create_plot(qtbot, filled_window, 'New Storyline')

    assert filled_window.novel.plots
    assert filled_window.novel.plots[-1].text == 'New Storyline'

    persisted_novel = client.fetch_novel(view.novel.id)
    assert len(persisted_novel.plots) == len(view.novel.plots)
    assert persisted_novel.plots[-1].text == 'New Storyline'


def test_delete_dramatic_question(qtbot, filled_window: MainWindow, monkeypatch):
    view: NovelView = go_to_novel(filled_window)
    click_on_item(qtbot, view.ui.wdgDramaticQuestions.tableView, 0, SelectionItemsModel.ColName)
    assert len(view.novel.plots) == 3
    plot = view.novel.plots[0]
    assert plot == view.novel.scenes[0].plot_values[0].plot

    patch_confirmed(monkeypatch)
    view.ui.wdgDramaticQuestions.btnRemove.click()

    assert len(view.novel.plots) == 2
    assert plot not in view.novel.plots
    assert not view.novel.scenes[0].plot_values


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
