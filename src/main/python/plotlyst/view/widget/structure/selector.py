"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QPushButton, QWidget, QToolButton
from overrides import overrides
from qthandy import translucent, pointy, incr_icon, incr_font, clear_layout, hbox
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from plotlyst.common import RELAXED_WHITE_COLOR, RED_COLOR, truncate_string, act_color
from plotlyst.core.domain import Novel, StoryBeat, \
    Scene, StoryBeatType
from plotlyst.event.core import EventListener, Event
from plotlyst.event.handler import event_dispatchers
from plotlyst.events import NovelStoryStructureUpdated
from plotlyst.service.cache import acts_registry
from plotlyst.view.common import action, restyle, ButtonPressResizeEventFilter
from plotlyst.view.icons import IconRegistry
from plotlyst.view.style.base import apply_white_menu


class StructureBeatSelectorMenu(MenuWidget):
    selected = pyqtSignal(StoryBeat)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)
        apply_white_menu(self)
        self.aboutToShow.connect(self._fillUp)

    def _fillUp(self):
        self.clear()

        self.addSection('Associate this scene to a story structure beat')
        self.addSeparator()

        act = 1
        if self.novel.active_story_structure.acts():
            self.addSection(f'Act {act}', IconRegistry.act_icon(act))
        self.addSeparator()
        for beat in self.novel.active_story_structure.beats:
            if beat.type == StoryBeatType.BEAT and beat.enabled:
                tip = beat.notes if beat.notes else ''
                if tip:
                    tip = truncate_string(tip, 125)
                else:
                    tip = beat.placeholder if beat.placeholder else beat.description
                beat_action = action(beat.text, IconRegistry.from_name(beat.icon, beat.icon_color),
                                     slot=partial(self.selected.emit, beat),
                                     tooltip=tip)
                beat_action.setDisabled(acts_registry.occupied(beat))
                self.addAction(beat_action)
            if beat.ends_act:
                act += 1
                self.addSection(f'Act {act}', IconRegistry.act_icon(act))
                self.addSeparator()

        self._frame.updateGeometry()


class StructureBeatSelectorButton(QPushButton):
    selected = pyqtSignal(StoryBeat)
    removed = pyqtSignal()

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self._scene: Optional[Scene] = None
        self._beat: Optional[StoryBeat] = None

        pointy(self)
        self._offFilter = OpacityEventFilter(self)
        self._onFilter = OpacityEventFilter(self, leaveOpacity=1.0, enterOpacity=0.7)
        self.installEventFilter(ButtonPressResizeEventFilter(self))
        incr_icon(self, 4)
        incr_font(self)
        self.reset()

        self._selectorMenu = StructureBeatSelectorMenu(self.novel)
        self._selectorMenu.selected.connect(self.selected)
        self._contextMenu = MenuWidget()
        self._contextMenu.addAction(
            action('Unlink beat', IconRegistry.from_name('fa5s.unlink', RED_COLOR), slot=self.removed))

        self.clicked.connect(self._showMenu)

    def setScene(self, scene: Scene):
        beat = scene.beat(self.novel)
        if beat:
            self.setBeat(beat)
            self._activate()
        else:
            self.reset()

    def setBeat(self, beat: StoryBeat):
        self._beat = beat
        self._activate()

    def reset(self):
        self._beat = None
        self.setText('Beat')
        self.setIcon(IconRegistry.story_structure_icon())
        self.setToolTip('Select a beat from story structure')
        self.setStyleSheet('''
            QPushButton::menu-indicator {
                width: 0px;
            }
            QPushButton {
                border: 2px dotted grey;
                border-radius: 6px;
                padding: 4px;
                font: italic;
            }
            QPushButton:hover {
                border: 2px dotted #4B0763;
                color: #4B0763;
                font: normal;
            }
        ''')
        restyle(self)
        self.removeEventFilter(self._onFilter)
        self.installEventFilter(self._offFilter)
        translucent(self, 0.4)

    def _activate(self):
        self.setText(self._beat.text)
        self.setIcon(IconRegistry.from_name(self._beat.icon, self._beat.icon_color))
        self.setToolTip(self._beat.description)
        self.setStyleSheet(f'''
            QPushButton::menu-indicator {{
                width: 0px;
            }}
            QPushButton {{
                border: 2px solid {self._beat.icon_color};
                border-radius: 10px;
                padding: 6px;
                background: {RELAXED_WHITE_COLOR};
            }}
        ''')
        restyle(self)
        self.removeEventFilter(self._offFilter)
        self.installEventFilter(self._onFilter)
        translucent(self, 1.0)

    def _showMenu(self):
        if self._beat:
            self._contextMenu.exec(QCursor.pos())
        else:
            self._selectorMenu.exec(QCursor.pos())


class ActToolButton(QToolButton):
    def __init__(self, act: int, parent=None):
        super().__init__(parent)
        self.act = act
        self.setProperty('base', True)
        pointy(self)
        self.setIcon(IconRegistry.from_name(f'mdi.numeric-{act}-circle', color='grey', color_on=act_color(act)))
        self.setCheckable(True)


class ActSelectorButtons(QWidget, EventListener):
    actToggled = pyqtSignal(int, bool)
    actClicked = pyqtSignal(int, bool)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel: Novel = novel
        self._buttons: Dict[int, ActToolButton] = {}
        hbox(self)
        event_dispatchers.instance(self._novel).register(self, NovelStoryStructureUpdated)
        self.refresh()

    @overrides
    def event_received(self, event: Event):
        self.refresh()

    def setActChecked(self, act: int, checked: bool):
        if act in self._buttons.keys():
            self._buttons[act].setChecked(checked)

    def refresh(self):
        clear_layout(self)
        self._buttons.clear()
        if self._novel is None:
            return

        acts: int = self._novel.active_story_structure.acts()
        if not acts:
            return

        for act in range(1, acts + 1):
            btn = ActToolButton(act)
            self._buttons[act] = btn
            btn.setChecked(True)
            btn.toggled.connect(partial(self.actToggled.emit, act))
            btn.clicked.connect(partial(self.actClicked.emit, act))
            self.layout().addWidget(btn)

    def actFilters(self) -> Dict[int, bool]:
        filters = {}
        for act, btn in self._buttons.items():
            filters[act] = btn.isChecked()

        return filters
