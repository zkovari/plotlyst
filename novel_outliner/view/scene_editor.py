from typing import Optional

import qtawesome
from PyQt5.QtCore import QObject, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from novel_outliner.core.client import client
from novel_outliner.core.domain import Novel, Scene, ACTION_SCENE, REACTION_SCENE, Event
from novel_outliner.model.characters_model import CharactersSceneAssociationTableModel
from novel_outliner.model.novel import NovelStoryLinesListModel
from novel_outliner.view.common import EditorCommand
from novel_outliner.view.generated.scene_editor_ui import Ui_SceneEditor
from novel_outliner.view.icons import IconRegistry


class SceneEditor(QObject):
    commands_sent = pyqtSignal(QWidget, list)

    def __init__(self, novel: Novel, scene: Optional[Scene] = None):
        super().__init__()
        self.widget = QWidget()
        self.ui = Ui_SceneEditor()
        self.ui.setupUi(self.widget)
        self.novel = novel

        if scene:
            self.scene = scene
            self._new_scene = False
        else:
            self.scene = Scene('')
            self._new_scene = True

        self.ui.tabWidget.setTabIcon(self.ui.tabWidget.indexOf(self.ui.tabGeneral), IconRegistry.general_info_icon())
        self.ui.btnVeryUnhappy.setIcon(qtawesome.icon('fa5s.sad-cry', color_on='red'))
        self.ui.btnUnHappy.setIcon(qtawesome.icon('mdi.emoticon-sad', color_on='yellow'))
        self.ui.btnNeutral.setIcon(qtawesome.icon('mdi.emoticon-neutral', color_on='orange'))
        self.ui.btnHappy.setIcon(qtawesome.icon('fa5s.smile', color_on='lightgreen'))
        self.ui.btnVeryHappy.setIcon(qtawesome.icon('fa5s.smile-beam', color_on='darkgreen'))

        self.ui.btnAddEvent.setIcon(IconRegistry.plus_icon())
        self.ui.btnRemoveEvent.setIcon(IconRegistry.minus_icon())

        self.ui.cbPov.addItem('', None)
        for char in self.novel.characters:
            self.ui.cbPov.addItem(char.name, char)
        if self.scene.pov:
            self.ui.cbPov.setCurrentText(self.scene.pov.name)

        self.ui.sbDay.setValue(self.scene.day)

        self.ui.cbType.setItemIcon(0, IconRegistry.custom_scene_icon())
        self.ui.cbType.setItemIcon(1, IconRegistry.action_scene_icon())
        self.ui.cbType.setItemIcon(2, IconRegistry.reaction_scene_icon())
        self.ui.cbType.currentTextChanged.connect(self._on_type_changed)
        if self.scene.type:
            self.ui.cbType.setCurrentText(self.scene.type)
        else:
            self.ui.cbType.setCurrentIndex(1)
        self._on_type_changed(self.ui.cbType.currentText())

        self.ui.textEvent1.setText(self.scene.beginning)
        self.ui.textEvent2.setText(self.scene.middle)
        self.ui.textEvent3.setText(self.scene.end)

        self.ui.lineTitle.setText(self.scene.title)
        self.ui.textSynopsis.setText(self.scene.synopsis)
        self.ui.cbWip.setChecked(self.scene.wip)
        self.ui.cbPivotal.setChecked(self.scene.pivotal)
        self.ui.cbEndCreatesEvent.setChecked(self.scene.end_event)

        self._characters_model = CharactersSceneAssociationTableModel(self.novel, self.scene)
        self._characters_proxy_model = QSortFilterProxyModel()
        self._characters_proxy_model.setSourceModel(self._characters_model)
        self.ui.tblCharacters.setModel(self._characters_proxy_model)

        self.story_line_model = NovelStoryLinesListModel(self.novel)
        self.ui.lstStoryLines.setModel(self.story_line_model)
        for story_line in self.scene.story_lines:
            self.story_line_model.selected.add(story_line)
        self.story_line_model.modelReset.emit()

        self.btn_save = self.ui.buttonBox.button(QDialogButtonBox.Save)
        self.btn_save.setShortcut('Ctrl+S')
        self.btn_save.clicked.connect(self._on_saved)
        self.btn_cancel = self.ui.buttonBox.button(QDialogButtonBox.Cancel)
        self.btn_cancel.setShortcut('Esc')
        self.btn_cancel.clicked.connect(self._on_cancel)

    def _on_type_changed(self, text: str):
        if text == ACTION_SCENE:
            self.ui.lblType1.setText('Goal:')
            self.ui.lblType2.setText('Conflict:')
            self.ui.lblType3.setText('Disaster:')
        elif text == REACTION_SCENE:
            self.ui.lblType1.setText('Reaction:')
            self.ui.lblType2.setText('Dilemma:')
            self.ui.lblType3.setText('Decision:')
        else:
            self.ui.lblType1.setText('Beginning:')
            self.ui.lblType2.setText('Middle:')
            self.ui.lblType3.setText('End:')

    def _on_saved(self):
        self.scene.title = self.ui.lineTitle.text()
        self.scene.synopsis = self.ui.textSynopsis.toPlainText()
        self.scene.type = self.ui.cbType.currentText()
        self.scene.beginning = self.ui.textEvent1.toPlainText()
        self.scene.middle = self.ui.textEvent2.toPlainText()
        self.scene.end = self.ui.textEvent3.toPlainText()
        self.scene.day = self.ui.sbDay.value()
        pov = self.ui.cbPov.currentData()
        if pov:
            self.scene.pov = pov
        self.scene.wip = self.ui.cbWip.isChecked()
        self.scene.pivotal = self.ui.cbPivotal.isChecked()

        self.scene.story_lines.clear()
        for story_line in self.story_line_model.selected:
            self.scene.story_lines.append(story_line)

        if self._new_scene:
            self.novel.scenes.append(self.scene)
            self.scene.sequence = self.novel.scenes.index(self.scene)
            client.insert_scene(self.novel, self.scene)
        else:
            client.update_scene(self.scene)

        events = []
        self.scene.end_event = self.ui.cbEndCreatesEvent.isChecked()
        if self.scene.end_event:
            events.append(Event(event=self.scene.end, day=self.scene.day))
        client.replace_scene_events(self.novel, self.scene, events)
        self.commands_sent.emit(self.widget, [EditorCommand.CLOSE_CURRENT_EDITOR,
                                              EditorCommand.DISPLAY_SCENES])

    def _on_cancel(self):
        self.commands_sent.emit(self.widget, [EditorCommand.CLOSE_CURRENT_EDITOR, EditorCommand.DISPLAY_SCENES])
