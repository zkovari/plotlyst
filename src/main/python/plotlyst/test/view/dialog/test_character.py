from src.main.python.plotlyst.test.common import show_widget
from src.main.python.plotlyst.view.dialog.character import BackstoryEditorDialog


def test_backstory_editor(qtbot):
    diag = BackstoryEditorDialog()
    show_widget(qtbot, diag)

    assert not diag.btnSave.isEnabled()
    qtbot.keyClicks(diag.lineKeyphrase, 'Test')
    assert diag.btnSave.isEnabled()

    diag.btnVeryUnhappy.click()
