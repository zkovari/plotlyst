from typing import List

from PyQt5.QtWidgets import QMessageBox, QAction

from src.main.python.plotlyst.core.domain import Scene
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel
from src.main.python.plotlyst.test.common import create_character, start_new_scene_editor, assert_data, go_to_scenes, \
    click_on_item, popup_actions_on_item, trigger_popup_action_on_item
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.scenes_view import ScenesOutlineView


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


def test_scene_deletion(qtbot, filled_window: MainWindow, monkeypatch):
    view: ScenesOutlineView = go_to_scenes(filled_window)
    click_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle)
    assert view.ui.btnEdit.isEnabled()
    assert view.ui.btnDelete.isEnabled()

    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.No)  # cancel
    view.ui.btnDelete.click()
    assert len(view.novel.scenes) == 2
    assert_data(view.tblModel, 'Scene 1', 0, ScenesTableModel.ColTitle)

    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)  # confirm
    view.ui.btnDelete.click()
    assert len(view.novel.scenes) == 1
    assert_data(view.tblModel, 'Scene 2', 0, ScenesTableModel.ColTitle)
    assert view.tblModel.rowCount() == 1


def test_scene_edition(qtbot, filled_window: MainWindow):
    view: ScenesOutlineView = go_to_scenes(filled_window)
    click_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle)
    assert view.ui.btnEdit.isEnabled()

    view.ui.btnEdit.click()
    assert view.editor

    title = 'New scene title'
    view.editor.ui.lineTitle.clear()
    qtbot.keyClicks(view.editor.ui.lineTitle, title)
    view.editor.ui.btnClose.click()
    assert not view.editor

    assert_data(view.tblModel, title, 0, ScenesTableModel.ColTitle)


def test_context_menu(qtbot, filled_window: MainWindow):
    view: ScenesOutlineView = go_to_scenes(filled_window)
    actions: List[QAction] = popup_actions_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle)
    assert len(actions) == 2
    assert actions[0].text() == 'Toggle WIP status'
    assert actions[1].text() == 'Insert new scene'


def test_toggle_wip_status(qtbot, filled_window: MainWindow):
    view: ScenesOutlineView = go_to_scenes(filled_window)
    trigger_popup_action_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle, 'Toggle WIP status')
    assert view.novel.scenes[0].wip
