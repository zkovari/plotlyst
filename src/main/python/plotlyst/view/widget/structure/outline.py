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
import copy
import uuid
from functools import partial
from typing import Optional

from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QEnterEvent, QResizeEvent
from PyQt6.QtWidgets import QWidget, QDialog
from overrides import overrides
from qthandy import line, vbox, margins, hbox, spacer, sp, incr_icon, transparent, italic
from qthandy.filter import OpacityEventFilter

from plotlyst.common import PLOTLYST_SECONDARY_COLOR
from plotlyst.core.domain import StoryBeat, StoryBeatType, midpoints, hook_beat, motion_beat, \
    disturbance_beat, characteristic_moment_beat, normal_world_beat, general_beat, turn_beat, twist_beat, StoryStructure
from plotlyst.view.common import label, scrolled, push_btn, wrap, tool_btn
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.widget.display import PopupDialog, Icon
from plotlyst.view.widget.outline import OutlineTimelineWidget, OutlineItemWidget
from plotlyst.view.widget.structure.beat import BeatsPreview
from plotlyst.view.widget.structure.timeline import StoryStructureTimelineWidget


class StoryStructureBeatWidget(OutlineItemWidget):
    actChanged = pyqtSignal()

    def __init__(self, beat: StoryBeat, structure: StoryStructure, parent=None):
        self.beat = beat
        super().__init__(beat, parent)
        self._structure = structure
        self._allowActs = structure.custom
        self._structurePreview: Optional[StoryStructureTimelineWidget] = None
        self._text.setText(self.beat.notes)
        self._text.setMaximumSize(220, 110)
        self._btnIcon.removeEventFilter(self._dragEventFilter)
        self._btnIcon.setCursor(Qt.CursorShape.ArrowCursor)
        self.setAcceptDrops(False)
        self._initStyle(name=self.beat.text,
                        desc=self.beat.placeholder if self.beat.placeholder else self.beat.description,
                        tooltip=self.beat.description)

        if self._allowActs:
            self._btnEndsAct = tool_btn(IconRegistry.act_icon(self.beat.act + 1, self._structure, 'grey'),
                                        transparent_=True, checkable=True,
                                        parent=self)
            self._btnEndsAct.installEventFilter(OpacityEventFilter(self._btnEndsAct, ignoreCheckedButton=True))
            self._btnEndsAct.setChecked(self.beat.ends_act)
            self._btnEndsAct.setHidden(True)
            self._btnEndsAct.toggled.connect(self._actEndChanged)

    def attachStructurePreview(self, structurePreview: 'StoryStructureTimelineWidget'):
        self._structurePreview = structurePreview

    @overrides
    def enterEvent(self, event: QEnterEvent) -> None:
        if self.beat not in midpoints and not self.beat.ends_act:
            super().enterEvent(event)
        if self._structurePreview:
            self._structurePreview.highlightBeat(self.beat)
        if self._allowActs:
            self._btnEndsAct.setIcon(IconRegistry.act_icon(self.beat.act + 1, self._structure, 'grey'))
            self._btnEndsAct.setVisible(True)

    @overrides
    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        if self._structurePreview:
            self._structurePreview.unhighlightBeats()
        if self._allowActs:
            self._btnEndsAct.setVisible(False)

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._allowActs:
            self._btnEndsAct.setGeometry(5, self.iconFixedSize, 25, 25)

    @overrides
    def mimeType(self) -> str:
        return ''

    @overrides
    def _color(self) -> str:
        return self.beat.icon_color

    @overrides
    def _icon(self) -> QIcon:
        qcolor = QColor(self.beat.icon_color)
        qcolor.setAlpha(self._colorAlpha)
        return IconRegistry.from_name(self.beat.icon, qcolor)

    @overrides
    def _textChanged(self):
        self.beat.notes = self._text.toPlainText()
        self.changed.emit()

    def _actEndChanged(self, toggled: bool):
        self.beat.ends_act = toggled
        self.changed.emit()
        self.actChanged.emit()


class _StoryBeatSection(QWidget):
    def __init__(self, beat: StoryBeat, parent=None):
        super().__init__(parent)
        vbox(self, 0, spacing=0)

        self._label = push_btn(IconRegistry.from_name(beat.icon, beat.icon_color),
                               text=beat.text, transparent_=True,
                               tooltip=beat.description, checkable=True, icon_resize=False,
                               pointy_=False)
        self.btnAdd = push_btn(IconRegistry.plus_icon(PLOTLYST_SECONDARY_COLOR), 'Add')
        italic(self.btnAdd)
        self.btnAdd.setStyleSheet(f'border: 0px; color: {PLOTLYST_SECONDARY_COLOR};')
        self.layout().addWidget(group(self._label, spacer(), self.btnAdd, margin=0))
        desc = label(beat.description, description=True, wordWrap=True)
        self.layout().addWidget(wrap(desc, margin_left=20))

        self.setMinimumWidth(450)


class StoryBeatSelectorPopup(PopupDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wdgTitle = QWidget()
        self._beat: Optional[StoryBeat] = None

        self._scrollarea, self._wdgCenter = scrolled(self.frame, frameless=True, h_on=False)
        self._scrollarea.setProperty('transparent', True)
        transparent(self._wdgCenter)
        vbox(self._wdgCenter, 10, spacing=8)
        margins(self._wdgCenter, bottom=20)
        hbox(self.wdgTitle)
        self.wdgTitle.layout().addWidget(spacer())
        icon = Icon()
        icon.setIcon(IconRegistry.story_structure_icon())
        incr_icon(icon, 4)
        self.wdgTitle.layout().addWidget(icon)
        self.wdgTitle.layout().addWidget(label('Common story structure beats', bold=True, h4=True))
        self.wdgTitle.layout().addWidget(spacer())
        self.wdgTitle.layout().addWidget(self.btnReset)

        self._wdgCenter.layout().addWidget(self.wdgTitle)
        margins(self._wdgCenter, right=20, top=15)

        self._addBeat(general_beat)
        self._addHeader('Beginning', IconRegistry.cause_icon())
        self._addBeat(hook_beat)
        self._addBeat(motion_beat)
        self._addBeat(disturbance_beat)
        self._addBeat(characteristic_moment_beat)
        self._addBeat(normal_world_beat)
        self._addHeader('Escalation', IconRegistry.rising_action_icon('black'))
        self._addBeat(turn_beat)
        self._addBeat(twist_beat)

        # self._addHeader('Midpoint', IconRegistry.from_name('mdi.middleware-outline'))
        # self._addBeat(midpoint_ponr)
        # self._addBeat(midpoint_mirror)
        # self._addBeat(midpoint_proactive)

        self.btnConfirm = push_btn(text='Close', properties=['base', 'positive'])
        sp(self.btnConfirm).h_exp()
        self.btnConfirm.clicked.connect(self.reject)

        self.frame.layout().addWidget(self.btnConfirm)

    def display(self) -> Optional[StoryBeat]:
        result = self.exec()
        if result == QDialog.DialogCode.Accepted:
            cloned_beat = copy.deepcopy(self._beat)
            cloned_beat.id = uuid.uuid4()
            cloned_beat.custom = True
            return cloned_beat

    def _addHeader(self, name: str, icon: QIcon):
        icon_ = Icon()
        icon_.setIcon(icon)
        header = label(name, bold=True)
        self._wdgCenter.layout().addWidget(group(icon_, header), alignment=Qt.AlignmentFlag.AlignLeft)
        self._wdgCenter.layout().addWidget(line(color='lightgrey'))

    def _addBeat(self, beat: StoryBeat):
        wdg = _StoryBeatSection(beat)
        margins(wdg, left=15)
        self._wdgCenter.layout().addWidget(wdg)
        wdg.btnAdd.clicked.connect(partial(self._addClicked, beat))

    def _addClicked(self, beat: StoryBeat):
        self._beat = beat
        self.accept()


class StoryStructureOutline(OutlineTimelineWidget):
    beatChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._structureTimeline: Optional[StoryStructureTimelineWidget] = None
        self._beatsPreview: Optional[BeatsPreview] = None
        self._structure: Optional[StoryStructure] = None

    def attachStructurePreview(self, structureTimeline: StoryStructureTimelineWidget):
        self._structureTimeline = structureTimeline
        for wdg in self._beatWidgets:
            wdg.attachStructurePreview(self._structureTimeline)

    def attachBeatsPreview(self, beats: BeatsPreview):
        self._beatsPreview = beats

    @overrides
    def setStructure(self, structure: StoryStructure):
        self.clear()
        self._structure = structure
        self._items = structure.beats

        for item in self._structure.sorted_beats():
            if item.type == StoryBeatType.BEAT and item.enabled:
                self._addBeatWidget(item)
        if not self._items:
            self.layout().addWidget(self._newPlaceholderWidget(displayText=True))

        self.update()

    @overrides
    def _newBeatWidget(self, item: StoryBeat) -> StoryStructureBeatWidget:
        widget = StoryStructureBeatWidget(item, self._structure, parent=self)
        widget.attachStructurePreview(self._structureTimeline)
        widget.changed.connect(self.beatChanged)
        widget.actChanged.connect(self._actChanged)
        widget.removed.connect(self._beatRemovedClicked)

        return widget

    def _beatRemovedClicked(self, wdg: StoryStructureBeatWidget):
        def teardown():
            if self._beatsPreview:
                QTimer.singleShot(150, self._beatsPreview.refresh)

        if wdg.beat.custom:
            self._structureTimeline.removeBeat(wdg.beat)
            self._beatRemoved(wdg, teardownFunction=teardown)
        else:
            wdg.beat.enabled = False
            self._structureTimeline.toggleBeatVisibility(wdg.beat)
            self._beatWidgetRemoved(wdg, teardownFunction=teardown)

    @overrides
    def _placeholderClicked(self, placeholder: QWidget):
        self._currentPlaceholder = placeholder
        beat = StoryBeatSelectorPopup.popup()
        if beat:
            self._insertBeat(beat)

    def _insertBeat(self, beat: StoryBeat):
        def teardown():
            if self._beatsPreview:
                self._structureTimeline.insertBeat(beat)
                QTimer.singleShot(150, self._beatsPreview.refresh)

        if self._structure.acts == 0:
            beat.act = 0

        wdg = self._newBeatWidget(beat)
        i = self.layout().indexOf(self._currentPlaceholder)
        if i > 0:
            percentBefore = self.layout().itemAt(i - 1).widget().beat.percentage
            if i < self.layout().count() - 1:
                percentAfter = self.layout().itemAt(i + 1).widget().beat.percentage
            else:
                percentAfter = 99
            beat.percentage = percentBefore + (percentAfter - percentBefore) / 2
        self._insertWidget(beat, wdg, teardownFunction=teardown)

    def _actChanged(self):
        self._structureTimeline.refreshActs()
        self.timelineChanged.emit()