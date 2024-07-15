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
from enum import Enum, auto
from functools import partial
from typing import Optional, List, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QPushButton, QDialog, QScrollArea, QApplication, QDialogButtonBox, QLabel
from qthandy import vspacer, spacer, transparent, bold, vbox, incr_font, \
    hbox, margins, underline, line, pointy
from qtmenu import MenuWidget

from plotlyst.common import ACT_THREE_COLOR
from plotlyst.core.domain import StoryStructure, Novel, StoryBeat, \
    save_the_cat, three_act_structure, heros_journey, hook_beat, motion_beat, \
    disturbance_beat, normal_world_beat, characteristic_moment_beat, midpoint, midpoint_ponr, midpoint_mirror, \
    midpoint_proactive, crisis, first_plot_point, first_plot_point_ponr, first_plot_points, midpoints
from plotlyst.view.common import ExclusiveOptionalButtonGroup, push_btn
from plotlyst.view.generated.story_structure_selector_dialog_ui import Ui_StoryStructureSelectorDialog
from plotlyst.view.icons import IconRegistry
from plotlyst.view.layout import group
from plotlyst.view.style.base import apply_white_menu
from plotlyst.view.widget.display import IconText
from plotlyst.view.widget.input import Toggle
from plotlyst.view.widget.structure.beat import BeatsPreview
from plotlyst.view.widget.structure.outline import StoryStructureTimelineWidget


class _AbstractStructureEditor(QWidget):
    def __init__(self, novel: Novel, structure: StoryStructure, parent=None):
        super(_AbstractStructureEditor, self).__init__(parent)
        self._structure = structure
        vbox(self)
        self.wdgTitle = IconText(self)
        self.wdgTitle.setText(structure.title)
        if structure.icon:
            self.wdgTitle.setIcon(IconRegistry.from_name(structure.icon, structure.icon_color))
        bold(self.wdgTitle)
        incr_font(self.wdgTitle, 2)
        self.wdgCustom = QWidget()

        self.wdgPreview = StoryStructureTimelineWidget(self)
        self.wdgPreview.setCheckOccupiedBeats(False)
        self.wdgPreview.setBeatsMoveable(True)
        self.wdgPreview.setActsClickable(False)
        self.wdgPreview.setActsResizeable(True)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        vbox(self._scroll)

        self.beatsPreview = BeatsPreview(novel, checkOccupiedBeats=False)
        self._scroll.setWidget(self.beatsPreview)
        self.beatsPreview.attachStructurePreview(self.wdgPreview)
        self.wdgPreview.setStructure(novel, self._structure)
        self.beatsPreview.setStructure(self._structure)
        self.layout().addWidget(self.wdgTitle)
        self.layout().addWidget(line())
        self.layout().addWidget(self.wdgCustom)
        self.layout().addWidget(vspacer(20))
        self.layout().addWidget(self.wdgPreview)
        self.layout().addWidget(self._scroll)

        # self.wdgPreview.actsResized.connect(lambda: emit_event(NovelStoryStructureUpdated(self)))
        # self.wdgPreview.beatMoved.connect(lambda: emit_event(NovelStoryStructureUpdated(self)))

    def structure(self) -> StoryStructure:
        return self._structure


class BeatCustomization(Enum):
    pass


class _ThreeActBeginning(BeatCustomization):
    Hook = auto()
    Disturbance = auto()
    Motion = auto()
    Characteristic_moment = auto()
    Normal_world = auto()


class _ThreeActFirstPlotPoint(BeatCustomization):
    First_plot_point = auto()
    Point_of_no_return = auto()


class _ThreeActMidpoint(BeatCustomization):
    Turning_point = auto()
    Point_of_no_return = auto()
    Mirror_moment = auto()
    Proactive = auto()


class _ThreeActEnding(BeatCustomization):
    Crisis = auto()


def beat_option_title(option: BeatCustomization) -> str:
    return option.name.replace('_', ' ')


def beat_option_description(option: BeatCustomization) -> str:
    if option == _ThreeActBeginning.Hook:
        return hook_beat.description
    elif option == _ThreeActBeginning.Motion:
        return motion_beat.description
    elif option == _ThreeActBeginning.Disturbance:
        return disturbance_beat.description
    elif option == _ThreeActBeginning.Normal_world:
        return normal_world_beat.description
    elif option == _ThreeActBeginning.Characteristic_moment:
        return characteristic_moment_beat.description

    elif option == _ThreeActFirstPlotPoint.First_plot_point:
        return first_plot_point.description
    elif option == _ThreeActFirstPlotPoint.Point_of_no_return:
        return first_plot_point_ponr.description

    elif option == _ThreeActMidpoint.Turning_point:
        return midpoint.description
    elif option == _ThreeActMidpoint.Point_of_no_return:
        return midpoint_ponr.description
    elif option == _ThreeActMidpoint.Mirror_moment:
        return midpoint_mirror.description
    elif option == _ThreeActMidpoint.Proactive:
        return midpoint_proactive.description

    elif option == _ThreeActEnding.Crisis:
        return crisis.description


def beat_option_icon(option: BeatCustomization) -> Tuple[str, str]:
    if option == _ThreeActBeginning.Hook:
        return hook_beat.icon, hook_beat.icon_color
    elif option == _ThreeActBeginning.Motion:
        return motion_beat.icon, motion_beat.icon_color
    elif option == _ThreeActBeginning.Disturbance:
        return disturbance_beat.icon, disturbance_beat.icon_color
    elif option == _ThreeActBeginning.Normal_world:
        return normal_world_beat.icon, normal_world_beat.icon_color
    elif option == _ThreeActBeginning.Characteristic_moment:
        return characteristic_moment_beat.icon, characteristic_moment_beat.icon_color

    elif option == _ThreeActFirstPlotPoint.First_plot_point:
        return first_plot_point.icon, first_plot_point.icon_color
    elif option == _ThreeActFirstPlotPoint.Point_of_no_return:
        return first_plot_point_ponr.icon, first_plot_point_ponr.icon_color

    elif option == _ThreeActMidpoint.Turning_point:
        return midpoint.icon, midpoint.icon_color
    elif option == _ThreeActMidpoint.Point_of_no_return:
        return midpoint_ponr.icon, midpoint_ponr.icon_color
    elif option == _ThreeActMidpoint.Mirror_moment:
        return midpoint_mirror.icon, midpoint_mirror.icon_color
    elif option == _ThreeActMidpoint.Proactive:
        return midpoint_proactive.icon, midpoint_proactive.icon_color

    elif option == _ThreeActEnding.Crisis:
        return crisis.icon, crisis.icon_color


def option_from_beat(beat: StoryBeat) -> Optional[BeatCustomization]:
    if beat == hook_beat:
        return _ThreeActBeginning.Hook
    elif beat == motion_beat:
        return _ThreeActBeginning.Motion
    elif beat == disturbance_beat:
        return _ThreeActBeginning.Disturbance
    elif beat == normal_world_beat:
        return _ThreeActBeginning.Normal_world
    elif beat == characteristic_moment_beat:
        return _ThreeActBeginning.Characteristic_moment

    elif beat == first_plot_point:
        return _ThreeActFirstPlotPoint.First_plot_point
    elif beat == first_plot_point_ponr:
        return _ThreeActFirstPlotPoint.Point_of_no_return

    elif beat == midpoint:
        return _ThreeActMidpoint.Turning_point
    elif beat == midpoint_ponr:
        return _ThreeActMidpoint.Point_of_no_return
    elif beat == midpoint_mirror:
        return _ThreeActMidpoint.Mirror_moment
    elif beat == midpoint_proactive:
        return _ThreeActMidpoint.Proactive

    elif beat == crisis:
        return _ThreeActEnding.Crisis

    return None


def find_first_plot_point(structure: StoryStructure) -> Optional[StoryBeat]:
    return next((x for x in structure.beats if x in first_plot_points), None)


def find_midpoint(structure: StoryStructure) -> Optional[StoryBeat]:
    return next((x for x in structure.beats if x in midpoints), None)


def find_crisis(structure: StoryStructure) -> Optional[StoryBeat]:
    return next((x for x in structure.beats if x == crisis), None)


class BeatOptionToggle(QWidget):
    def __init__(self, option: BeatCustomization, parent=None):
        super(BeatOptionToggle, self).__init__(parent)
        hbox(self, spacing=0)
        self.option = option
        self.toggle = Toggle()
        self.layout().addWidget(self.toggle, alignment=Qt.AlignmentFlag.AlignTop)
        desc = QLabel(beat_option_description(option))
        desc.setProperty('description', True)
        btnTitle = QPushButton(beat_option_title(option))
        btnTitle.setIcon(IconRegistry.from_name(*beat_option_icon(option)))
        pointy(btnTitle)
        transparent(btnTitle)
        btnTitle.clicked.connect(self.toggle.click)
        wdgTop = QWidget()
        vbox(wdgTop, 0)
        wdgTop.layout().addWidget(btnTitle, alignment=Qt.AlignmentFlag.AlignLeft)
        wdgTop.layout().addWidget(desc)
        self.layout().addWidget(wdgTop)
        self.layout().addWidget(spacer())


class ActOptionsButton(QPushButton):
    def __init__(self, text: str, act: int, parent=None):
        super(ActOptionsButton, self).__init__(text, parent)
        pointy(self)

        self.setProperty('structure-customization', True)
        if act == 1:
            self.setProperty('act-one', True)
        elif act == 2:
            self.setProperty('act-two', True)
        else:
            self.setProperty('act-three', True)


class StructureOptionsWidget(QWidget):
    optionSelected = pyqtSignal(BeatCustomization)
    optionsReset = pyqtSignal()

    def __init__(self, options: List[BeatCustomization], parent=None, checked: Optional[BeatCustomization] = None):
        super(StructureOptionsWidget, self).__init__(parent)
        vbox(self)
        self.btnGroup = ExclusiveOptionalButtonGroup()
        for opt in options:
            wdg = BeatOptionToggle(opt)
            self.layout().addWidget(wdg)
            self.btnGroup.addButton(wdg.toggle)
            if opt == checked:
                wdg.toggle.setChecked(True)

            wdg.toggle.clicked.connect(partial(self._clicked, opt))

    def _clicked(self, option: BeatCustomization, checked: bool):
        if not checked:
            if not self.btnGroup.checkedButton():
                self.optionsReset.emit()
            return

        self.optionSelected.emit(option)


class StructureOptionsMenu(MenuWidget):
    def __init__(self, parent: QWidget, title: str, options: List[BeatCustomization],
                 checked: Optional[BeatCustomization] = None):
        super(StructureOptionsMenu, self).__init__(parent)
        apply_white_menu(self)
        self.addSection(title)
        self.addSeparator()

        self.options = StructureOptionsWidget(options, self, checked=checked)
        self.addWidget(self.options)


class _ThreeActStructureEditor(_AbstractStructureEditor):
    def __init__(self, novel: Novel, structure: StoryStructure, parent=None):
        super().__init__(novel, structure, parent)

        hbox(self.wdgCustom)
        margins(self.wdgCustom, top=20)

        self.lblCustomization = QLabel('Customization:')
        underline(self.lblCustomization)
        bold(self.lblCustomization)

        self.btnBeginning = ActOptionsButton('Beginning', 1)
        self.btnBeginning.setIcon(IconRegistry.cause_icon())
        checked = option_from_beat(structure.beats[0])
        menu = StructureOptionsMenu(self.btnBeginning, 'Select the beginning',
                                    [_ThreeActBeginning.Hook, _ThreeActBeginning.Disturbance,
                                     _ThreeActBeginning.Motion, _ThreeActBeginning.Characteristic_moment,
                                     _ThreeActBeginning.Normal_world], checked=checked)
        menu.options.optionSelected.connect(self._beginningChanged)
        menu.options.optionsReset.connect(self._beginningReset)

        self.btnFirstPlotPoint = ActOptionsButton('First Plot Point', 1)
        self.btnFirstPlotPoint.setIcon(IconRegistry.from_name('mdi6.chevron-double-right'))
        fpp_beat = find_first_plot_point(self._structure)
        checked = _ThreeActFirstPlotPoint.Point_of_no_return if fpp_beat == first_plot_point_ponr else None
        menu = StructureOptionsMenu(self.btnFirstPlotPoint, 'Customize',
                                    [_ThreeActFirstPlotPoint.Point_of_no_return], checked=checked)
        menu.options.optionSelected.connect(self._firstPlotPointChanged)
        menu.options.optionsReset.connect(self._firstPlotPointReset)

        self.btnMidpoint = ActOptionsButton('Midpoint', 2)
        self.btnMidpoint.setIcon(IconRegistry.from_name('mdi.middleware-outline', '#2e86ab'))

        midpoint_beat = find_midpoint(self._structure)
        checked = option_from_beat(midpoint_beat) if midpoint_beat else None
        menu = StructureOptionsMenu(self.btnMidpoint, 'Select the midpoint',
                                    [_ThreeActMidpoint.Turning_point, _ThreeActMidpoint.Point_of_no_return,
                                     _ThreeActMidpoint.Mirror_moment, _ThreeActMidpoint.Proactive], checked=checked)
        menu.options.optionSelected.connect(self._midpointChanged)
        menu.options.optionsReset.connect(self._midpointReset)

        crisis_beat = find_crisis(self._structure)
        checked = option_from_beat(crisis_beat) if crisis_beat else None
        self.btnEnding = ActOptionsButton('Ending', 3)
        self.btnEnding.setIcon(IconRegistry.reversed_cause_and_effect_icon())
        menu = StructureOptionsMenu(self.btnEnding, 'Extend the ending',
                                    [_ThreeActEnding.Crisis], checked=checked)
        menu.options.optionSelected.connect(self._endingChanged)
        menu.options.optionsReset.connect(self._endingReset)

        self.toggle4act = Toggle()
        self.toggle4act.setChecked(midpoint_beat.ends_act)

        wdg = group(spacer(), self.btnBeginning, self.btnFirstPlotPoint, self.btnMidpoint,
                    self.btnEnding, spacer(), spacing=15)
        wdg.layout().insertWidget(1, self.lblCustomization, alignment=Qt.AlignmentFlag.AlignTop)
        lbl = push_btn(text='Split 2nd act into two parts', transparent_=True)
        lbl.clicked.connect(self.toggle4act.animateClick)
        wdg.layout().addWidget(group(lbl, self.toggle4act, spacing=0, margin=0))
        self.toggle4act.toggled.connect(self._mindpointSplit)
        self.wdgCustom.layout().addWidget(wdg)

    def _beginningChanged(self, beginning: _ThreeActBeginning):
        if beginning == _ThreeActBeginning.Hook:
            beat = hook_beat
        elif beginning == _ThreeActBeginning.Motion:
            beat = motion_beat
        elif beginning == _ThreeActBeginning.Disturbance:
            beat = disturbance_beat
        elif beginning == _ThreeActBeginning.Normal_world:
            beat = normal_world_beat
        elif beginning == _ThreeActBeginning.Characteristic_moment:
            beat = characteristic_moment_beat
        else:
            return
        self.beatsPreview.replaceBeat(self._structure.beats[0], copy.deepcopy(beat))

    def _beginningReset(self):
        self.beatsPreview.replaceBeat(self._structure.beats[0], copy.deepcopy(three_act_structure.beats[0]))

    def _firstPlotPointChanged(self, option: _ThreeActFirstPlotPoint):
        if option == _ThreeActFirstPlotPoint.Point_of_no_return:
            beat = first_plot_point_ponr
        else:
            beat = first_plot_point

        current_pp = find_first_plot_point(self._structure)
        if current_pp:
            self.beatsPreview.replaceBeat(current_pp, copy.deepcopy(beat))

    def _firstPlotPointReset(self):
        current_pp = find_first_plot_point(self._structure)
        if current_pp:
            self.beatsPreview.replaceBeat(current_pp, copy.deepcopy(first_plot_point))

    def _midpointChanged(self, midpoint_option: _ThreeActMidpoint):
        if midpoint_option == _ThreeActMidpoint.Turning_point:
            beat = midpoint
        elif midpoint_option == _ThreeActMidpoint.Point_of_no_return:
            beat = midpoint_ponr
        elif midpoint_option == _ThreeActMidpoint.Mirror_moment:
            beat = midpoint_mirror
        elif midpoint_option == _ThreeActMidpoint.Proactive:
            beat = midpoint_proactive
        else:
            return

        current_midpoint = find_midpoint(self._structure)
        if current_midpoint:
            self.beatsPreview.replaceBeat(current_midpoint, copy.deepcopy(beat))

    def _midpointReset(self):
        current_midpoint = find_midpoint(self._structure)
        if current_midpoint:
            self.beatsPreview.replaceBeat(current_midpoint, copy.deepcopy(midpoint))

    def _mindpointSplit(self, split: bool):
        current_midpoint = find_midpoint(self._structure)
        if current_midpoint:
            current_midpoint.ends_act = split
            self.wdgPreview.refreshActs()

    def _endingChanged(self, ending_option: _ThreeActEnding):
        self.beatsPreview.insertBeat(copy.deepcopy(crisis))

    def _endingReset(self):
        self.beatsPreview.removeBeat(crisis)


class _SaveTheCatActStructureEditor(_AbstractStructureEditor):
    def __init__(self, novel: Novel, structure: StoryStructure, parent=None):
        super(_SaveTheCatActStructureEditor, self).__init__(novel, structure, parent)


class _HerosJourneyStructureEditor(_AbstractStructureEditor):
    def __init__(self, novel: Novel, structure: StoryStructure, parent=None):
        super(_HerosJourneyStructureEditor, self).__init__(novel, structure, parent)


class StoryStructureSelectorDialog(QDialog, Ui_StoryStructureSelectorDialog):
    def __init__(self, novel: Novel, structure: Optional[StoryStructure] = None, parent=None):
        super(StoryStructureSelectorDialog, self).__init__(parent)
        self.setupUi(self)
        self._novel = novel
        self.setWindowIcon(IconRegistry.story_structure_icon())
        self.btnThreeAct.setIcon(IconRegistry.from_name('mdi.numeric-3-circle-outline', color_on=ACT_THREE_COLOR))
        self.btnSaveTheCat.setIcon(IconRegistry.from_name('fa5s.cat', color_on='white'))
        self.btnHerosJourney.setIcon(IconRegistry.from_name('fa5s.mask', color_on='white'))
        self.buttonGroup.buttonClicked.connect(self._structureChanged)

        self._structure: Optional[StoryStructure] = None
        if structure:
            self.setWindowTitle('Story structure editor')
            self.btnCancel.setHidden(True)
            self.wdgTypesContainer.setHidden(True)
            page, clazz = self._pageAndClass(structure)
            self.__initEditor(structure, page, clazz, copyStructure=False)
        else:
            self._structureChanged()

    def structure(self) -> StoryStructure:
        return self._structure

    @staticmethod
    def display(novel: Novel, structure: Optional[StoryStructure] = None) -> Optional[StoryStructure]:
        dialog = StoryStructureSelectorDialog(novel, structure)
        screen = QApplication.screenAt(dialog.pos())
        if screen:
            dialog.resize(int(screen.size().width() * 0.9), int(screen.size().height() * 0.7))
        else:
            dialog.resize(600, 500)

        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return dialog.structure()

        return None

    def _structureChanged(self):
        if self.btnThreeAct.isChecked():
            self.__initEditor(three_act_structure, self.pageThreeAct, _ThreeActStructureEditor)
        elif self.btnSaveTheCat.isChecked():
            self.__initEditor(save_the_cat, self.pageSaveTheCat, _SaveTheCatActStructureEditor)
        elif self.btnHerosJourney.isChecked():
            self.__initEditor(heros_journey, self.pageHerosJourney, _HerosJourneyStructureEditor)

    def __initEditor(self, structure: StoryStructure, page: QWidget, clazz, copyStructure: bool = True):
        self.stackedWidget.setCurrentWidget(page)
        if page.layout().count() == 0:
            if copyStructure:
                self._structure = copy.deepcopy(structure)
            else:
                self._structure = structure
            page.layout().addWidget(clazz(self._novel, self._structure, self))
        else:
            self._structure = page.layout().itemAt(0).widget().structure()

    def _pageAndClass(self, structure: StoryStructure):
        if structure.title == three_act_structure.title:
            return self.pageThreeAct, _ThreeActStructureEditor
        elif structure.title == save_the_cat.title:
            return self.pageSaveTheCat, _SaveTheCatActStructureEditor
        elif structure.title == heros_journey.title:
            return self.pageHerosJourney, _HerosJourneyStructureEditor
