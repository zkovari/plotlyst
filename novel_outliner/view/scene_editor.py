from typing import Optional

import qtawesome
from PyQt5.QtCore import QObject, pyqtSignal, QSortFilterProxyModel, QModelIndex, QTimer
from PyQt5.QtWidgets import QWidget

from novel_outliner.core.client import client
from novel_outliner.core.domain import Novel, Scene, ACTION_SCENE, REACTION_SCENE, Event
from novel_outliner.model.characters_model import CharactersSceneAssociationTableModel
from novel_outliner.model.novel import NovelStoryLinesListModel
from novel_outliner.model.scenes_model import ScenesTableModel
from novel_outliner.view.common import EditorCommand, EditorCommandType
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

        self.ui.tabWidget.setTabIcon(self.ui.tabWidget.indexOf(self.ui.tabGeneral), IconRegistry.general_info_icon())
        self.ui.tabWidget.setTabIcon(self.ui.tabWidget.indexOf(self.ui.tabNotes), IconRegistry.notes_icon())

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

        self.ui.cbType.setItemIcon(0, IconRegistry.custom_scene_icon())
        self.ui.cbType.setItemIcon(1, IconRegistry.action_scene_icon())
        self.ui.cbType.setItemIcon(2, IconRegistry.reaction_scene_icon())
        self.ui.cbType.currentTextChanged.connect(self._on_type_changed)

        self.story_line_model = NovelStoryLinesListModel(self.novel)
        self.ui.lstStoryLines.setModel(self.story_line_model)
        self.story_line_model.selection_changed.connect(self._save_scene)

        self.scenes_model = ScenesTableModel(self.novel)
        self.ui.lstScenes.setModel(self.scenes_model)
        self.ui.lstScenes.setModelColumn(ScenesTableModel.ColTitle)
        self.ui.lstScenes.setMaximumWidth(200)
        self.ui.lstScenes.clicked.connect(self._new_scene_selected)

        self.ui.btnClose.clicked.connect(self._on_close)
        self.ui.btnPrevious.clicked.connect(self._on_previous_scene)
        self.ui.btnNext.clicked.connect(self._on_next_scene)

        self._save_timer = QTimer()
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self._save_scene)
        self._save_enabled = False
        self._update_view(scene)

        self.ui.cbWip.clicked.connect(self._save_scene)
        self.ui.cbPov.currentIndexChanged.connect(self._save_scene)
        self.ui.sbDay.valueChanged.connect(self._save_scene)
        self.ui.cbPivotal.currentIndexChanged.connect(self._save_scene)
        self.ui.cbBeginningType.currentIndexChanged.connect(self._save_scene)
        self.ui.cbEndingHook.currentIndexChanged.connect(self._save_scene)
        self.ui.cbType.currentIndexChanged.connect(self._save_scene)
        self.ui.textEvent1.textChanged.connect(self._pending_save)
        self.ui.textEvent2.textChanged.connect(self._pending_save)
        self.ui.textEvent3.textChanged.connect(self._pending_save)
        self.ui.lineTitle.textEdited.connect(self._pending_save)
        self.ui.textSynopsis.textChanged.connect(self._pending_save)
        self.ui.textNotes.textChanged.connect(self._pending_save)

    def _update_view(self, scene: Optional[Scene] = None):
        if scene:
            self.scene = scene
            self._new_scene = False
        else:
            self.scene = Scene('')
            self._new_scene = True

        if self.scene.pov:
            self.ui.cbPov.setCurrentText(self.scene.pov.name)

        self.ui.sbDay.setValue(self.scene.day)

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
        self.ui.cbPivotal.setCurrentText(self.scene.pivotal)
        self.ui.cbBeginningType.setCurrentText(self.scene.beginning_type)
        self.ui.cbEndingHook.setCurrentText(self.scene.ending_hook)
        self.ui.textNotes.setPlainText(self.scene.notes)

        self._characters_model = CharactersSceneAssociationTableModel(self.novel, self.scene)
        self._characters_model.selection_changed.connect(self._save_scene)
        self._characters_proxy_model = QSortFilterProxyModel()
        self._characters_proxy_model.setSourceModel(self._characters_model)
        self.ui.tblCharacters.setModel(self._characters_proxy_model)

        self.story_line_model.selected.clear()
        for story_line in self.scene.story_lines:
            self.story_line_model.selected.add(story_line)
        self.story_line_model.modelReset.emit()

        if self._new_scene:
            self.ui.btnPrevious.setDisabled(True)
            self.ui.btnPrevious.setHidden(True)
            self.ui.btnNext.setDisabled(True)
            self.ui.btnNext.setHidden(True)
        else:
            if self.scene.sequence == 0:
                self.ui.btnPrevious.setDisabled(True)
            elif self.scene.sequence == len(self.novel.scenes) - 1:
                self.ui.btnNext.setDisabled(True)

        self._save_enabled = True

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

    def _pending_save(self):
        if self._save_enabled:
            self._save_timer.start(500)

    def _save_scene(self):
        self._save_timer.stop()
        if not self._save_enabled:
            return

        self.scene.title = self.ui.lineTitle.text()
        self.scene.synopsis = self.ui.textSynopsis.toPlainText()
        self.scene.type = self.ui.cbType.currentText()
        self.scene.beginning = self.ui.textEvent1.toPlainText()
        self.scene.middle = self.ui.textEvent2.toPlainText()
        self.scene.end = self.ui.textEvent3.toPlainText()
        self.scene.day = self.ui.sbDay.value()
        self.scene.notes = self.ui.textNotes.toPlainText()
        pov = self.ui.cbPov.currentData()
        if pov:
            self.scene.pov = pov
        self.scene.wip = self.ui.cbWip.isChecked()
        self.scene.pivotal = self.ui.cbPivotal.currentText()
        self.scene.beginning_type = self.ui.cbBeginningType.currentText()
        self.scene.ending_hook = self.ui.cbEndingHook.currentText()
        self.scene.story_lines.clear()
        for story_line in self.story_line_model.selected:
            self.scene.story_lines.append(story_line)
        if self._new_scene:
            self.novel.scenes.append(self.scene)
            self.scene.sequence = self.novel.scenes.index(self.scene)
            client.insert_scene(self.novel, self.scene)
        else:
            client.update_scene(self.scene)
        self._new_scene = False
        events = []
        self.scene.end_event = True
        if self.scene.end_event:
            events.append(Event(event=self.scene.end, day=self.scene.day))
        client.replace_scene_events(self.novel, self.scene, events)

    def _on_close(self):
        self.commands_sent.emit(self.widget, [EditorCommand.close_editor(), EditorCommand.display_scenes()])

    def _on_previous_scene(self):
        self.commands_sent.emit(self.widget, [EditorCommand.close_editor(),
                                              EditorCommand(EditorCommandType.EDIT_SCENE, self.scene.sequence - 1)])

    def _on_next_scene(self):
        self.commands_sent.emit(self.widget, [EditorCommand.close_editor(),
                                              EditorCommand(EditorCommandType.EDIT_SCENE, self.scene.sequence + 1)])

    def _new_scene_selected(self, index: QModelIndex):
        scene = self.scenes_model.data(index, role=ScenesTableModel.SceneRole)
        self._save_enabled = False
        self._update_view(scene)
