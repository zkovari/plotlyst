from src.main.python.plotlyst.core.domain import Novel, BackstoryEvent, VERY_UNHAPPY
from src.main.python.plotlyst.test.common import show_widget, patch_confirmed
from src.main.python.plotlyst.view.character_editor import CharacterEditor
from src.main.python.plotlyst.view.dialog.character import BackstoryEditorDialog
from src.main.python.plotlyst.view.widget.characters import CharacterBackstoryEvent


def test_backstory(qtbot, monkeypatch):
    novel = Novel('Novel')
    editor = CharacterEditor(novel)
    show_widget(qtbot, editor.widget)

    assert editor.ui.wdgBackstory.layout().count() == 3  # lbl, control, spacer

    backstory = BackstoryEvent('Test', '', emotion=VERY_UNHAPPY, as_baby=True)
    monkeypatch.setattr(BackstoryEditorDialog, "display", lambda *args: backstory)
    editor.ui.btnNewBackstory.click()

    assert editor.ui.wdgBackstory.layout().count() == 5  # lbl, control, event, control, spacer

    event: CharacterBackstoryEvent = editor.ui.wdgBackstory.layout().itemAt(2).widget()
    assert event.card.lblKeyphrase.text() == backstory.keyphrase

    backstory.keyphrase = 'Changed'
    monkeypatch.setattr(BackstoryEditorDialog, "display", lambda *args: backstory)
    event.card.btnEdit.click()

    assert event.card.lblKeyphrase.text() == 'Changed'

    patch_confirmed(monkeypatch)
    event.card.btnRemove.click()
    assert editor.ui.wdgBackstory.layout().count() == 3
