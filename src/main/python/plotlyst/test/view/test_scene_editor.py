from plotlyst.core.domain import Novel, default_story_structures
from plotlyst.view.scene_editor import SceneEditor
from plotlyst.view.stylesheet import APP_STYLESHEET


def editor(qtbot, novel: Novel):
    editor = SceneEditor(novel)
    editor.widget.setStyleSheet(APP_STYLESHEET)
    editor.widget.show()
    qtbot.addWidget(editor.widget)
    qtbot.waitExposed(editor.widget, timeout=5000)

    return editor


def test_editor_with_new_scene(qtbot):
    novel = Novel('Test-novel', story_structures=default_story_structures)
    novel.story_structures[0].active = True
    view: SceneEditor = editor(qtbot, novel)
    scene = novel.new_scene()
    novel.scenes.append(scene)
    view.refresh()
    view.set_scene(scene)

    assert view.ui.wdgPov.btnAvatar.text() == 'POV'
