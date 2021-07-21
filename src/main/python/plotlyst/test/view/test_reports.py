from src.main.python.plotlyst.test.common import go_to_reports
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.reports_view import ReportsView


def test_reports_display(qtbot, filled_window: MainWindow):
    view: ReportsView = go_to_reports(filled_window)
    assert view.ui.tabWidget.currentWidget() == view.ui.tabStoryMap

    qtbot.wait(100)  # wait until painted
    view.ui.tabWidget.setCurrentWidget(view.ui.tabCharacters)
    view.ui.tabWidget_2.setCurrentWidget(view.ui.tabCharacterArcs)
    view.ui.tabWidget.setCurrentWidget(view.ui.tabStoryDistribution)
