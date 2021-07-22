from PyQt5.QtWidgets import QComboBox

from src.main.python.plotlyst.core.domain import VERY_UNHAPPY, UNHAPPY, NEUTRAL, VERY_HAPPY, HAPPY
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel
from src.main.python.plotlyst.test.common import go_to_reports, edit_item, click_on_item
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.reports_view import ReportsView


def test_reports_display(qtbot, filled_window: MainWindow):
    view: ReportsView = go_to_reports(filled_window)
    assert view.ui.tabWidget.currentWidget() == view.ui.tabStoryMap

    qtbot.wait(100)  # wait until painted
    view.ui.tabWidget.setCurrentWidget(view.ui.tabCharacters)
    view.ui.tabWidget_2.setCurrentWidget(view.ui.tabCharacterArcs)
    view.ui.tabWidget.setCurrentWidget(view.ui.tabStoryDistribution)


def test_edit_arc(qtbot, filled_window: MainWindow):
    view: ReportsView = go_to_reports(filled_window)

    view.ui.tabWidget.setCurrentWidget(view.ui.tabCharacters)
    view.ui.tabWidget_2.setCurrentWidget(view.ui.tabCharacterArcs)

    edit_func = lambda x: x.setCurrentIndex(0)
    edit_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColArc, QComboBox, edit_func)
    assert view.novel.scenes[0].pov_arc() == VERY_UNHAPPY

    click_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle)

    edit_func = lambda x: x.setCurrentIndex(1)
    edit_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColArc, QComboBox, edit_func)
    assert view.novel.scenes[0].pov_arc() == UNHAPPY

    click_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle)

    edit_func = lambda x: x.setCurrentIndex(2)
    edit_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColArc, QComboBox, edit_func)
    assert view.novel.scenes[0].pov_arc() == NEUTRAL

    click_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle)

    edit_func = lambda x: x.setCurrentIndex(3)
    edit_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColArc, QComboBox, edit_func)
    assert view.novel.scenes[0].pov_arc() == HAPPY

    click_on_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColTitle)

    edit_func = lambda x: x.setCurrentIndex(4)
    edit_item(qtbot, view.ui.tblScenes, 0, ScenesTableModel.ColArc, QComboBox, edit_func)
    assert view.novel.scenes[0].pov_arc() == VERY_HAPPY
