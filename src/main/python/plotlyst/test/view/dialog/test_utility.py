from src.main.python.plotlyst.test.common import show_widget
from src.main.python.plotlyst.view.dialog.utility import ArtbreederDialog


def test_artbreeder_picker(qtbot):
    diag = ArtbreederDialog()
    show_widget(qtbot, diag)

    diag.fetch()
