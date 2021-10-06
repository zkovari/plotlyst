from typing import Optional

from src.main.python.plotlyst.core.domain import Novel, Scene
from src.main.python.plotlyst.test.common import click_on_item
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
    novel = Novel('Test-novel')
    view: SceneEditor = editor(qtbot, novel)

    assert view.ui.cbType.currentIndex() == 1
    assert view.ui.cbType.currentText() == 'action'
    assert view.ui.cbPov.currentIndex() == 0
    assert view.ui.cbPov.currentText() == 'Select POV ...'


def test_editor_with_none_values(qtbot):
    novel = Novel('Test-novel')
    scene = Scene(title='')
    novel.scenes.append(scene)

    view: SceneEditor = editor(qtbot, novel, scene)

    assert view.ui.cbType.currentIndex() == 0


def test_display_scene_builder(qtbot):
    novel = Novel('Test-novel')
    view: SceneEditor = editor(qtbot, novel)

    view.ui.tabWidget.setCurrentWidget(view.ui.tabBuilder)


def test_editor_with_multiple_scenes(qtbot, test_client):
    novel = Novel('Test-novel')
    scene1 = Scene(title='Scene 1', beat=novel.story_structure.beats[0], sequence=0)
    scene2 = Scene(title='Scene 2', beat=novel.story_structure.beats[1], sequence=1)
    scene3 = Scene(title='Scene 3', sequence=2)
    novel.scenes.append(scene1)
    novel.scenes.append(scene2)
    novel.scenes.append(scene3)

    view: SceneEditor = editor(qtbot, novel, scene3)

    assert view.ui.lineTitle.text() == 'Scene 3'
    assert view.ui.cbPivotal.currentText() == 'Select story beat...'

    assert view.ui.btnPrevious.isEnabled()
    assert not view.ui.btnNext.isEnabled()

    view.ui.btnPrevious.click()
    assert view.ui.lineTitle.text() == 'Scene 2'
    assert view.ui.cbPivotal.currentText() == 'Inciting Incident'
    assert view.ui.btnPrevious.isEnabled()
    assert view.ui.btnNext.isEnabled()

    view.ui.btnPrevious.click()
    assert view.ui.lineTitle.text() == 'Scene 1'
    assert view.ui.cbPivotal.currentText() == 'Exposition'
    assert not view.ui.btnPrevious.isEnabled()
    assert view.ui.btnNext.isEnabled()

    view.ui.btnNext.click()
    assert view.ui.lineTitle.text() == 'Scene 2'
    assert view.ui.cbPivotal.currentText() == 'Inciting Incident'
    assert view.ui.btnPrevious.isEnabled()
    assert view.ui.btnNext.isEnabled()

    click_on_item(qtbot, view.ui.lstScenes, 2)
    assert view.ui.lineTitle.text() == 'Scene 2'
    assert view.ui.cbPivotal.currentText() == 'Inciting Incident'
    assert view.ui.btnPrevious.isEnabled()
    assert view.ui.btnNext.isEnabled()
