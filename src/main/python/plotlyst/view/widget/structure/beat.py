"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

This file is part of Plotlyst.

Plotlyst is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Plotlyst is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from functools import partial
from typing import Optional, Dict

import qtanim
from PyQt6.QtCore import Qt, QEvent, QObject, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QFrame, QGridLayout
from overrides import overrides
from qthandy import vspacer, translucent, transparent, gc, bold, clear_layout, retain_when_hidden, grid, decr_icon, \
    italic

from src.main.python.plotlyst.common import act_color, RELAXED_WHITE_COLOR
from src.main.python.plotlyst.core.domain import StoryStructure, Novel, StoryBeat, \
    Scene, StoryBeatType, midpoints
from src.main.python.plotlyst.env import app_env
from src.main.python.plotlyst.event.core import EventListener, Event, emit_event
from src.main.python.plotlyst.event.handler import event_dispatchers
from src.main.python.plotlyst.events import SceneChangedEvent, SceneDeletedEvent
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import DelayedSignalSlotConnector
from src.main.python.plotlyst.view.generated.beat_widget_ui import Ui_BeatWidget
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.widget.scenes import SceneStoryStructureWidget, SceneSelector


class BeatWidget(QFrame, Ui_BeatWidget, EventListener):
    beatHighlighted = pyqtSignal(StoryBeat)
    beatToggled = pyqtSignal(StoryBeat)

    def __init__(self, novel: Novel, beat: StoryBeat, checkOccupiedBeats: bool = True, parent=None,
                 toggleEnabled: bool = True):
        super().__init__(parent)
        self.setupUi(self)
        self._novel = novel
        self.beat = beat
        self._checkOccupiedBeats = checkOccupiedBeats
        self._toggleEnabled = toggleEnabled

        bold(self.lblTitle)
        bold(self.lblSceneTitle)
        italic(self.lblDescription)
        transparent(self.lblTitle)
        transparent(self.lblDescription)
        transparent(self.btnIcon)

        self.btnSceneSelector = SceneSelector(app_env.novel)
        decr_icon(self.btnSceneSelector, 2)
        retain_when_hidden(self.btnSceneSelector)
        self.layoutRight.insertWidget(0, self.btnSceneSelector,
                                      alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.btnSceneSelector.setHidden(True)
        self.btnSceneSelector.sceneSelected.connect(self._sceneLinked)
        transparent(self.wdgToggleParent)

        retain_when_hidden(self.cbToggle)

        self.cbToggle.setHidden(True)
        if not self._canBeToggled():
            self.cbToggle.setDisabled(True)
        self.cbToggle.toggled.connect(self._beatToggled)
        self.cbToggle.clicked.connect(self._beatClicked)
        self.cbToggle.setChecked(self.beat.enabled)

        self.scene: Optional[Scene] = None
        self.repo = RepositoryPersistenceManager.instance()

        self.updateInfo()
        self.refresh()

        self.installEventFilter(self)

        self._synopsisConnector = DelayedSignalSlotConnector(self.textSynopsis.textChanged, self._synopsisEdited,
                                                             parent=self)
        dispatcher = event_dispatchers.instance(self._novel)
        dispatcher.register(self, SceneChangedEvent, SceneDeletedEvent)

    def updateInfo(self):
        self.lblTitle.setText(self.beat.text)
        self.lblDescription.setText(self.beat.description)
        if self.beat.icon:
            self.btnIcon.setIcon(IconRegistry.from_name(self.beat.icon, self.beat.icon_color))

        self.lblTitle.setStyleSheet(f'''
            QLabel {{
                background-color: {RELAXED_WHITE_COLOR};
            }}
            QLabel:enabled {{color: {self.beat.icon_color};}}
            QLabel:disabled {{color:grey;}}
        ''')

    def refresh(self):
        self.stackedWidget.setCurrentWidget(self.pageInfo)
        if not self._checkOccupiedBeats:
            return

        self.scene = acts_registry.scene(self.beat)
        if self.scene:
            self.lblTitle.setEnabled(True)
            self.btnIcon.setEnabled(True)
            self.stackedWidget.setCurrentWidget(self.pageScene)
            self.lblSceneTitle.setText(self.scene.title)
            self.textSynopsis.setText(self.scene.synopsis)
            if self.scene.pov:
                self.btnPov.setIcon(avatars.avatar(self.scene.pov))
            if self.scene.purpose:
                self.btnSceneType.setIcon(IconRegistry.scene_type_icon(self.scene))
        else:
            self.lblTitle.setDisabled(True)
            self.btnIcon.setDisabled(True)
            self.textSynopsis.clear()

    @overrides
    def event_received(self, event: Event):
        self._synopsisConnector.freeze()
        self.refresh()
        self._synopsisConnector.freeze(False)

    @overrides
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            if self._canBeToggled() and self._infoPage():
                self.cbToggle.setVisible(True)
            self.btnSceneSelector.setVisible(self._infoPage() and self._checkOccupiedBeats and self.beat.enabled)
            self.setStyleSheet(f'.BeatWidget {{background-color: {act_color(self.beat.act, translucent=True)};}}')
            self.beatHighlighted.emit(self.beat)
        elif event.type() == QEvent.Type.Leave:
            self.cbToggle.setHidden(True)
            self.btnSceneSelector.setHidden(True)
            self.setStyleSheet(f'.BeatWidget {{background-color: {RELAXED_WHITE_COLOR};}}')

        return super().eventFilter(watched, event)

    def _infoPage(self) -> bool:
        return self.stackedWidget.currentWidget() == self.pageInfo

    def _scenePage(self) -> bool:
        return self.stackedWidget.currentWidget() == self.pageScene

    def _canBeToggled(self):
        if not self._toggleEnabled:
            return False
        if self.beat in midpoints or self.beat.ends_act:
            return False
        return True

    def _beatToggled(self, toggled: bool):
        translucent(self.lblDescription, 1 if toggled else 0.5)
        self.lblTitle.setEnabled(toggled)
        self.btnIcon.setEnabled(toggled)
        self.lblDescription.setEnabled(toggled)
        bold(self.lblTitle, toggled)

    def _beatClicked(self, checked: bool):
        self.beat.enabled = checked
        self.beatToggled.emit(self.beat)
        self.btnSceneSelector.setVisible(self._infoPage() and self._checkOccupiedBeats and self.beat.enabled)

    def _sceneLinked(self, scene: Scene):
        scene.link_beat(app_env.novel.active_story_structure, self.beat)
        self.repo.update_scene(self.scene)
        emit_event(self._novel, SceneChangedEvent(self, scene))
        self.refresh()
        qtanim.glow(self.lblTitle, color=QColor(self.beat.icon_color))

    def _synopsisEdited(self):
        if self.scene:
            self.scene.synopsis = self.textSynopsis.toPlainText()
            self.repo.update_scene(self.scene)
            emit_event(self._novel, SceneChangedEvent(self, self.scene))


class BeatsPreview(QFrame):
    def __init__(self, novel: Novel, checkOccupiedBeats: bool = True, toggleBeats: bool = True, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._checkOccupiedBeats = checkOccupiedBeats
        self._toggleBeats = toggleBeats
        self._layout: QGridLayout = grid(self)
        self._beats: Dict[StoryBeat, BeatWidget] = {}
        self._structurePreview: Optional[SceneStoryStructureWidget] = None
        self._structure: Optional[StoryStructure] = None

        self.setProperty('relaxed-white-bg', True)

    def attachStructurePreview(self, structurePreview: SceneStoryStructureWidget):
        self._structurePreview = structurePreview

    def setStructure(self, structure: StoryStructure):
        self._structure = structure
        self.refresh()

    def refresh(self):
        clear_layout(self._layout)
        self._beats.clear()
        row = 0
        col = 0
        for beat in self._structure.beats:
            if beat.type != StoryBeatType.BEAT:
                continue
            if not self._toggleBeats and not beat.enabled:
                continue
            wdg = self.__initBeatWidget(beat)
            self._beats[beat] = wdg
            if beat.act - 1 > col:  # new act
                self._layout.addWidget(vspacer(), row + 1, col)
                col = beat.act - 1
                row = 0
            self._layout.addWidget(wdg, row, col)
            row += 1

    def refreshBeat(self, beat: StoryBeat):
        wdg = self._beats[beat]
        wdg.updateInfo()
        self._structurePreview.refreshBeat(beat)

    def replaceBeat(self, oldBeat: StoryBeat, newBeat: StoryBeat):
        for i, beat in enumerate(self._structure.beats):
            if beat == oldBeat:
                self._structure.beats[i] = newBeat
                break
        oldWdg = self._beats.pop(oldBeat)
        newWdg = self.__initBeatWidget(newBeat)
        self._beats[newBeat] = newWdg
        self._layout.replaceWidget(oldWdg, newWdg)
        gc(oldWdg)
        self._structurePreview.replaceBeat(oldBeat, newBeat)

    def removeBeat(self, beat: StoryBeat):
        self._structure.beats.remove(beat)
        wdg = self._beats.pop(beat)
        self._layout.removeWidget(wdg)
        gc(wdg)
        self.refresh()
        self._structurePreview.removeBeat(beat)

    def insertBeat(self, newBeat: StoryBeat):
        insert_to = -1
        for i, beat in enumerate(self._structure.beats):
            if beat.percentage > newBeat.percentage:
                insert_to = i
                break
        self._structure.beats.insert(insert_to, newBeat)
        self.refresh()
        self._structurePreview.insertBeat(newBeat)

    def __initBeatWidget(self, beat: StoryBeat) -> BeatWidget:
        wdg = BeatWidget(self._novel, beat, self._checkOccupiedBeats, toggleEnabled=self._toggleBeats)
        wdg.setMinimumSize(200, 50)
        wdg.beatHighlighted.connect(self._structurePreview.highlightBeat)
        wdg.beatToggled.connect(partial(self._structurePreview.toggleBeatVisibility, beat))

        return wdg
