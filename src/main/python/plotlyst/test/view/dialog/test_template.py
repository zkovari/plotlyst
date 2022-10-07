from src.main.python.plotlyst.core.template import ProfileTemplate, default_character_profiles
from src.main.python.plotlyst.view.dialog.template import CharacterProfileEditorDialog


def new_diag(qtbot, template: ProfileTemplate) -> CharacterProfileEditorDialog:
    diag = CharacterProfileEditorDialog(template)
    qtbot.addWidget(diag)
    diag.show()
    qtbot.waitExposed(diag, timeout=5000)

    return diag


def test_default_template(qtbot):
    diag = new_diag(qtbot, default_character_profiles()[0])

    assert not diag.btnEnneagram.isEnabled()
    assert not diag.btnTraits.isEnabled()
    assert diag.btnMisbelief.isEnabled()
    assert not diag.btnMbti.isEnabled()

    assert diag.profile_editor.profile().elements
