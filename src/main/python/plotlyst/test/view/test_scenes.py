from typing import List

from PyQt5.QtChart import QPieSeries
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QMessageBox, QAction, QSpinBox

from src.main.python.plotlyst.model.scenes_model import ScenesTableModel, ScenesStageTableModel, ScenesNotesTableModel
from src.main.python.plotlyst.test.common import create_character, start_new_scene_editor, assert_data, go_to_scenes, \
    click_on_item, popup_actions_on_item, trigger_popup_action_on_item, patch_confirmed, edit_item
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.scenes_view import ScenesOutlineView


def test_create_new_scene(qtbot, filled_window: MainWindow):
    scenes: ScenesOutlineView = start_new_scene_editor(filled_window)

    qtbot.keyClicks(scenes.editor.ui.lineTitle, 'New scene')
    scenes.editor.ui.sbDay.setValue(1)

    scenes.editor.ui.btnClose.click()

    row = scenes.ui.tblScenes.model().rowCount() - 1
    assert_data(scenes.ui.tblScenes.model(), 'New scene', row, 1)
    assert filled_window.novel.scenes
    assert filled_window.novel.scenes[row].title == 'New scene'
    assert filled_window.novel.scenes[row].type == 'action'
    assert filled_window.novel.scenes[row].day == 1


def test_scene_characters(qtbot, filled_window: MainWindow):
    create_character(qtbot, filled_window, 'Tom')
    create_character(qtbot, filled_window, 'Bob')

    scenes: ScenesOutlineView = start_new_scene_editor(filled_window)
    qtbot.keyClicks(scenes.editor.ui.lineTitle, 'Scene 1')
    scenes.editor.ui.cbPov.setCurrentText('Tom')
    scenes.editor.ui.btnClose.click()

    scenes: ScenesOutlineView = start_new_scene_editor(filled_window)
    qtbot.keyClicks(scenes.editor.ui.lineTitle, 'Scene 2')
    scenes.editor.ui.cbPov.setCurrentText('Bob')
    scenes.editor.ui.btnClose.click()


def test_scene_deletion(qtbot, filled_window: MainWindow, monkeypatch):
    view: ScenesOutlineView = go_to_scenes(filled_window)
    view.ui.btnTableView.click()
    
    click_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle)
    assert view.ui.btnEdit.isEnabled()
    assert view.ui.btnDelete.isEnabled()

    patch_confirmed(monkeypatch, QMessageBox.No)
    view.ui.btnDelete.click()
    assert len(view.novel.scenes) == 2
    assert_data(view.tblModel, 'Scene 1', 0, ScenesTableModel.ColTitle)

    patch_confirmed(monkeypatch)
    view.ui.btnDelete.click()
    assert len(view.novel.scenes) == 1
    assert_data(view.tblModel, 'Scene 2', 0, ScenesTableModel.ColTitle)
    assert view.tblModel.rowCount() == 1


def test_scene_edition(qtbot, filled_window: MainWindow):
    view: ScenesOutlineView = go_to_scenes(filled_window)
    view.ui.btnTableView.click()
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


def test_insert_new_scene_after(qtbot, filled_window: MainWindow):
    view: ScenesOutlineView = go_to_scenes(filled_window)
    trigger_popup_action_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle, 'Insert new scene')

    assert len(view.novel.scenes) == 3
    assert_data(view.tblModel, 'Scene 1', 0, ScenesTableModel.ColTitle)
    assert_data(view.tblModel, 'Untitled', 1, ScenesTableModel.ColTitle)
    assert_data(view.tblModel, 'Scene 2', 2, ScenesTableModel.ColTitle)


def test_switch_views(qtbot, filled_window: MainWindow):
    view: ScenesOutlineView = go_to_scenes(filled_window)

    view.ui.btnTableView.click()
    assert view.ui.tblScenes.verticalHeader().isVisible()

    view.ui.btnActionsView.click()
    assert_data(view.tblModel, 'Beginning', 0, ScenesTableModel.ColBeginning)
    assert_data(view.tblModel, 'Middle', 0, ScenesTableModel.ColMiddle)
    assert_data(view.tblModel, 'End', 0, ScenesTableModel.ColEnd)
    assert view.ui.tblScenes.verticalHeader().isVisible()

    view.ui.btnStatusView.click()
    assert view.stagesModel
    assert view.stagesProgress
    assert view.ui.tblSceneStages.verticalHeader().isVisible()
    charts = view.stagesProgress.charts()
    assert len(charts) == 4
    pie_series: QPieSeries = charts[0].chart.series()[0]
    assert pie_series.count() == 2
    assert pie_series.slices()[0].percentage() == 0.5


def test_change_stage(qtbot, filled_window: MainWindow):
    view: ScenesOutlineView = go_to_scenes(filled_window)

    view.ui.btnStatusView.click()
    assert view.stagesModel
    assert view.stagesProgress

    click_on_item(qtbot, view.ui.tblSceneStages, 0, ScenesStageTableModel.ColNoneStage)

    assert view.novel.scenes[0].stage is None

    charts = view.stagesProgress.charts()
    assert len(charts) == 4
    pie_series: QPieSeries = charts[0].chart.series()[0]
    assert pie_series.count() == 2
    assert pie_series.slices()[0].percentage() == 0.0

    click_on_item(qtbot, view.ui.tblSceneStages, 0, ScenesStageTableModel.ColNoneStage + 2)
    assert view.novel.scenes[0].stage == view.novel.stages[1]

    pie_series = charts[0].chart.series()[0]
    assert pie_series.slices()[0].percentage() == 0.5

    click_on_item(qtbot, view.ui.tblSceneStages, 0, ScenesStageTableModel.ColNoneStage + 3)
    assert view.novel.scenes[0].stage == view.novel.stages[2]

    pie_series = charts[0].chart.series()[0]
    assert pie_series.slices()[0].percentage() == 0.5


def test_timeline_display(qtbot, filled_window: MainWindow):
    view: ScenesOutlineView = go_to_scenes(filled_window)
    view.ui.btnTimelineView.click()

    assert view.ui.pageTimeline.isVisible()
    view.timeline_view.timeline_widget.grab().toImage()
    assert_data(view.timeline_view.model, 'Scene 1', 0, ScenesNotesTableModel.ColTitle)
    assert_data(view.timeline_view.model, 'Scene 2', 1, ScenesNotesTableModel.ColTitle)

    assert_data(view.timeline_view.model, 1, 0, ScenesNotesTableModel.ColTime)
    assert_data(view.timeline_view.model, 2, 1, ScenesNotesTableModel.ColTime)

    # mimic drawing curves
    filled_window.setWindowState(Qt.WindowNoState)
    filled_window.resize(300, 300)

    view.timeline_view.timeline_widget.grab().toImage()


def _edit_day(editor: QSpinBox):
    editor.setValue(3)


def test_edit_day(qtbot, filled_window: MainWindow):
    view: ScenesOutlineView = go_to_scenes(filled_window)
    view.ui.btnTimelineView.click()

    view.timeline_view.timeline_widget.grab().toImage()

    qtbot.wait(10)
    edit_item(qtbot, view.timeline_view.ui.tblScenes, 0, ScenesTableModel.ColTime, QSpinBox, _edit_day)
    assert view.novel.scenes[0].day == 3


def test_character_distribution_display(qtbot, filled_window: MainWindow):
    def assert_painted(index: QModelIndex):
        assert index.data(role=Qt.BackgroundRole) == QBrush(QColor('darkblue'))

    def assert_not_painted(index: QModelIndex):
        assert index.data(role=Qt.BackgroundRole) is None

    view: ScenesOutlineView = go_to_scenes(filled_window)
    view.ui.btnCharactersDistributionView.click()

    assert view.characters_distribution.ui.spinAverage.value() == 3
    model = view.characters_distribution.ui.tblSceneDistribution.model()
    assert_painted(model.index(0, 1))
    assert_painted(model.index(0, 2))
    assert_painted(model.index(1, 1))
    assert_painted(model.index(1, 2))
    assert_painted(model.index(2, 1))
    assert_not_painted(model.index(2, 2))
    assert_not_painted(model.index(3, 1))
    assert_painted(model.index(3, 2))
    assert_not_painted(model.index(4, 1))
    assert_not_painted(model.index(4, 2))

    # click brushed scene cell
    click_on_item(qtbot, view.characters_distribution.ui.tblSceneDistribution, 0, 1)
    assert model.flags(model.index(3, 0)) == Qt.NoItemFlags
    assert model.flags(model.index(4, 0)) == Qt.NoItemFlags

    # click empty area
    click_on_item(qtbot, view.characters_distribution.ui.tblSceneDistribution, 3, 1)
    assert model.flags(model.index(3, 0)) & Qt.ItemIsEnabled
    assert model.flags(model.index(4, 0)) & Qt.ItemIsEnabled
