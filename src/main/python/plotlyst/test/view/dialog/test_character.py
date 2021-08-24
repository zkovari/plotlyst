from src.main.python.plotlyst.test.common import show_widget
from src.main.python.plotlyst.view.dialog.character import BackstoryEditorDialog


def test_backstory_editor(qtbot):
    diag = BackstoryEditorDialog()
    show_widget(qtbot, diag)

    assert not diag.btnSave.isEnabled()
    qtbot.keyClicks(diag.lineKeyphrase, 'Test')
    assert diag.btnSave.isEnabled()

    diag.btnVeryUnhappy.click()
    diag.btnBaby.click()
    assert diag.lblAge.text() == '0-3'
    diag.btnChild.click()
    assert diag.lblAge.text() == '3-12'
    diag.btnTeenager.click()
    assert diag.lblAge.text() == '12-18'
    diag.btnAdult.click()
    assert diag.lblAge.text() == 'Adulthood'
