from src.main.python.plotlyst.core.domain import Novel, BackstoryEvent, VERY_UNHAPPY
from src.main.python.plotlyst.test.common import show_widget
from src.main.python.plotlyst.view.character_editor import CharacterEditor
from src.main.python.plotlyst.view.dialog.character import BackstoryEditorDialog


def test_backstory_add(qtbot, monkeypatch):
    novel = Novel('Novel')
    editor = CharacterEditor(novel)
    show_widget(qtbot, editor.widget)

    backstory = BackstoryEvent('Test', '', emotion=VERY_UNHAPPY, as_baby=True)
    monkeypatch.setattr(BackstoryEditorDialog, "display", lambda *args: backstory)
    editor.ui.btnNewBackstory.click()

    assert editor.ui.wdgBackstory.layout().count() == 1
