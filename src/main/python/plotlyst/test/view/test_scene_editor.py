from typing import Optional

from PyQt5.QtCore import Qt

from src.main.python.plotlyst.core.domain import Novel, Scene, default_story_structures
from src.main.python.plotlyst.view.scene_editor import SceneEditor
from src.main.python.plotlyst.view.stylesheet import APP_STYLESHEET


def editor(qtbot, novel: Novel, scene: Optional[Scene] = None):
    editor = SceneEditor(novel, scene)
    editor.widget.setStyleSheet(APP_STYLESHEET)
    editor.widget.show()
    qtbot.addWidget(editor.widget)
    qtbot.waitExposed(editor.widget, timeout=5000)

    return editor


def test_editor_with_new_scene(qtbot):
    novel = Novel('Test-novel', story_structures=default_story_structures)
    novel.story_structures[0].active = True
    view: SceneEditor = editor(qtbot, novel)

    assert view.ui.wdgPov.btnPov.text() == 'Select POV'
    assert view.ui.wdgPov.btnPov.toolButtonStyle() == Qt.ToolButtonTextUnderIcon
