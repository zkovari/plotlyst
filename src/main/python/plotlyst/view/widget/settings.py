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
from typing import Dict, Optional, List

import qtanim
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QEvent
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtWidgets import QWidget, QPushButton, QToolButton, QGridLayout
from overrides import overrides
from qthandy import transparent, sp, vbox, hbox, vspacer, incr_font, pointy, grid, margins
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from plotlyst.common import PLOTLYST_SECONDARY_COLOR, PLOTLYST_TERTIARY_COLOR
from plotlyst.core.domain import Novel, NovelSetting
from plotlyst.event.core import emit_event, EventListener, Event
from plotlyst.event.handler import event_dispatchers
from plotlyst.events import NovelMindmapToggleEvent, NovelPanelCustomizationEvent, \
    NovelStructureToggleEvent, NovelStorylinesToggleEvent, NovelCharactersToggleEvent, NovelScenesToggleEvent, \
    NovelWorldBuildingToggleEvent, NovelManuscriptToggleEvent, NovelDocumentsToggleEvent, NovelManagementToggleEvent, \
    NovelEmotionTrackingToggleEvent, NovelMotivationTrackingToggleEvent, NovelConflictTrackingToggleEvent, \
    NovelPovTrackingToggleEvent
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.common import label, ButtonPressResizeEventFilter
from plotlyst.view.icons import IconRegistry
from plotlyst.view.style.base import apply_white_menu
from plotlyst.view.style.button import apply_button_palette_color
from plotlyst.view.widget.input import Toggle

setting_titles: Dict[NovelSetting, str] = {
    NovelSetting.Structure: 'Story structure',
    NovelSetting.Mindmap: 'Events map',
    NovelSetting.Storylines: 'Storylines',
    NovelSetting.Characters: 'Characters',
    NovelSetting.Scenes: 'Scenes',
    NovelSetting.Track_emotion: 'Track character emotions',
    NovelSetting.Track_motivation: 'Track character motivation',
    NovelSetting.Track_conflict: 'Track character conflicts',
    NovelSetting.World_building: 'World-building',
    NovelSetting.Manuscript: 'Manuscript',
    NovelSetting.Documents: 'Documents',
    NovelSetting.Management: 'Task management',
    NovelSetting.Track_pov: 'Point of view'
}
setting_descriptions: Dict[NovelSetting, str] = {
    NovelSetting.Structure: "Follow a story structure to help you with your story's pacing and escalation",
    NovelSetting.Mindmap: "Visualize your story's events in a mindmap. Ideal for brainstorming or any other stage in writing",
    NovelSetting.Storylines: "Create separate storylines for plot, character's change, subplots, or relationship plots",
    NovelSetting.Characters: "Create a cast of characters with different roles, personalities, backstories, goals, and relationships among them",
    NovelSetting.Scenes: "Create scene cards for early outlining or later revision purposes to have characters, conflicts, or storylines associated to the scenes",
    NovelSetting.Track_emotion: "Track and visualize how characters' emotions shift between positive and negative throughout the scenes",
    NovelSetting.Track_motivation: "Track and visualize how characters' motivation change throughout the scenes",
    NovelSetting.Track_conflict: 'Track the frequency and the type of conflicts the characters face',
    NovelSetting.World_building: "[BETA] Develop your story's world by creating fictional settings and lore",
    NovelSetting.Manuscript: "Write your story in Plotlyst using the manuscript panel",
    NovelSetting.Documents: "Add documents for your planning or research",
    NovelSetting.Management: "Stay organized by tracking your tasks in a simple Kanban board",
    NovelSetting.Track_pov: "Track the point of view characters of your story"
}

panel_events = [NovelMindmapToggleEvent, NovelCharactersToggleEvent,
                NovelManuscriptToggleEvent, NovelScenesToggleEvent,
                NovelDocumentsToggleEvent, NovelStructureToggleEvent,
                NovelStorylinesToggleEvent, NovelWorldBuildingToggleEvent,
                NovelManagementToggleEvent]

setting_events: Dict[NovelSetting, NovelPanelCustomizationEvent] = {
    NovelSetting.Structure: NovelStructureToggleEvent,
    NovelSetting.Mindmap: NovelMindmapToggleEvent,
    NovelSetting.Storylines: NovelStorylinesToggleEvent,
    NovelSetting.Characters: NovelCharactersToggleEvent,
    NovelSetting.Scenes: NovelScenesToggleEvent,
    NovelSetting.Track_emotion: NovelEmotionTrackingToggleEvent,
    NovelSetting.Track_motivation: NovelMotivationTrackingToggleEvent,
    NovelSetting.Track_conflict: NovelConflictTrackingToggleEvent,
    NovelSetting.Track_pov: NovelPovTrackingToggleEvent,
    NovelSetting.World_building: NovelWorldBuildingToggleEvent,
    NovelSetting.Manuscript: NovelManuscriptToggleEvent,
    NovelSetting.Documents: NovelDocumentsToggleEvent,
    NovelSetting.Management: NovelManagementToggleEvent
}


def setting_icon(setting: NovelSetting, color=PLOTLYST_SECONDARY_COLOR, color_on=PLOTLYST_SECONDARY_COLOR) -> QIcon:
    if setting == NovelSetting.Structure:
        return IconRegistry.story_structure_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Mindmap:
        return IconRegistry.from_name('ri.mind-map', color, color_on=color_on)
    elif setting == NovelSetting.Storylines:
        return IconRegistry.storylines_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Characters:
        return IconRegistry.character_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Scenes:
        return IconRegistry.scene_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Track_emotion:
        return IconRegistry.emotion_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Track_motivation:
        return IconRegistry.from_name('fa5s.fist-raised', color=color, color_on=color_on)
    elif setting == NovelSetting.Track_conflict:
        return IconRegistry.conflict_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Track_pov:
        return IconRegistry.eye_open_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.World_building:
        return IconRegistry.world_building_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Manuscript:
        return IconRegistry.manuscript_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Documents:
        return IconRegistry.document_edition_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Management:
        return IconRegistry.board_icon(color, color_on)
    return QIcon()


def toggle_setting(source, novel: Novel, setting: NovelSetting, toggled: bool):
    novel.prefs.settings[setting.value] = toggled
    RepositoryPersistenceManager.instance().update_novel(novel)

    event_clazz = setting_events[setting]
    emit_event(novel, event_clazz(source, setting, toggled))


class NovelSettingBase(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


class NovelSettingToggle(QWidget):
    settingToggled = pyqtSignal(NovelSetting, bool)

    def __init__(self, novel: Novel, setting: NovelSetting, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._setting = setting

        self._title = QPushButton()
        self._title.setText(setting_titles[setting])
        self._title.setIcon(setting_icon(setting))
        apply_button_palette_color(self._title, PLOTLYST_SECONDARY_COLOR)
        transparent(self._title)
        incr_font(self._title, 2)

        self._description = label(setting_descriptions[setting], description=True)
        self._description.setWordWrap(True)
        sp(self._description).h_exp()

        self._wdgTitle = QWidget()
        vbox(self._wdgTitle)
        self._wdgTitle.layout().addWidget(self._title, alignment=Qt.AlignmentFlag.AlignLeft)
        self._wdgTitle.layout().addWidget(self._description)

        self._wdgChildren = QWidget()
        vbox(self._wdgChildren)
        margins(self._wdgChildren, left=20, right=20)
        self._wdgChildren.setHidden(True)

        self._toggle = Toggle()
        self._toggle.setChecked(True)
        self._toggle.toggled.connect(self._toggled)
        self._toggle.clicked.connect(self._clicked)

        self._wdgHeader = QWidget()
        self._wdgHeader.setObjectName('wdgHeader')
        hbox(self._wdgHeader)
        self._wdgHeader.layout().addWidget(self._wdgTitle)
        self._wdgHeader.layout().addWidget(self._toggle, alignment=Qt.AlignmentFlag.AlignTop)

        vbox(self, 0, 0)
        self.layout().addWidget(self._wdgHeader)
        self.layout().addWidget(self._wdgChildren)

        self._toggle.setChecked(self._novel.prefs.toggled(self._setting))

    def setChecked(self, checked: bool):
        self._toggle.setChecked(checked)

    def addChild(self, child: QWidget):
        self._wdgChildren.setVisible(self._toggle.isChecked())
        self._wdgChildren.layout().addWidget(child)

    def _toggled(self, toggled: bool):
        self._wdgTitle.setEnabled(toggled)
        self._wdgChildren.setVisible(toggled)

    def _clicked(self, toggled: bool):
        self.settingToggled.emit(self._setting, toggled)


class NovelPovSettingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


class NovelPanelCustomizationToggle(QToolButton):
    def __init__(self, setting: NovelSetting, parent=None):
        super().__init__(parent)
        self._setting = setting

        pointy(self)
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        self.setIcon(setting_icon(self._setting, 'grey', PLOTLYST_SECONDARY_COLOR))
        transparent(self)
        self.setIconSize(QSize(30, 30))
        self.setText(setting_titles[self._setting])
        incr_font(self, 2)

        sp(self).h_exp().v_exp()

        self.setMinimumWidth(150)
        self.setMaximumHeight(100)

        self.installEventFilter(ButtonPressResizeEventFilter(self))
        self.installEventFilter(OpacityEventFilter(self, ignoreCheckedButton=True))

        self.setStyleSheet(f'''
            QToolButton {{
                color: grey;
                background: lightgrey;
                border: 1px solid lightgrey;
                border-radius: 2px;
            }}
            QToolButton:checked {{
                color: black;
                background: {PLOTLYST_TERTIARY_COLOR};
            }}
        ''')

        self.clicked.connect(self._glow)

    def setting(self) -> NovelSetting:
        return self._setting

    def _glow(self, checked: bool):
        if checked:
            qtanim.glow(self, 150, color=QColor(PLOTLYST_SECONDARY_COLOR), radius=12)
        else:
            qtanim.glow(self, 150, color=QColor('grey'), radius=5)


class NovelPanelSettingsWidget(QWidget):
    clicked = pyqtSignal(NovelSetting, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel: Optional[Novel] = None
        self.setProperty('relaxed-white-bg', True)

        vbox(self)
        self._wdgCenter = QWidget()
        self._wdgBottom = QWidget()
        self._lblDesc = label('', wordWrap=True, description=True)
        incr_font(self._lblDesc, 2)
        self._lblDesc.setMinimumSize(400, 100)
        self._lblDesc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox(self._wdgBottom, margin=15).addWidget(self._lblDesc, alignment=Qt.AlignmentFlag.AlignCenter)

        self.layout().addWidget(label('Customize your experience:'),
                                alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._wdgCenter)
        self.layout().addWidget(self._wdgBottom)
        self._grid: QGridLayout = grid(self._wdgCenter)

        self._settings: Dict[NovelSetting, NovelPanelCustomizationToggle] = {}
        self._addSetting(NovelSetting.Manuscript, 0, 0)
        self._addSetting(NovelSetting.Characters, 0, 1)
        self._addSetting(NovelSetting.Scenes, 0, 2)

        self._addSetting(NovelSetting.Mindmap, 1, 0)
        self._addSetting(NovelSetting.Storylines, 1, 1)
        self._addSetting(NovelSetting.Structure, 1, 2)

        self._addSetting(NovelSetting.Documents, 2, 0)
        self._addSetting(NovelSetting.World_building, 2, 1)
        self._addSetting(NovelSetting.Management, 2, 2)

    def setNovel(self, novel: Novel):
        self._novel = novel
        for toggle in self._settings.values():
            toggle.setChecked(self._novel.prefs.toggled(toggle.setting()))

    # def reset(self):
    #     event_dispatchers.instance(self._novel).deregister(self, *panel_events)
    #     self._novel = None

    @overrides
    def eventFilter(self, watched: 'QObject', event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            self._lblDesc.setText(setting_descriptions[watched.setting()])
        return super().eventFilter(watched, event)

    def checkAllSettings(self, checked: bool):
        for k in self._settings.keys():
            self._settings[k].setChecked(checked)

    def checkSettings(self, settings: List[NovelSetting], checked: bool = True):
        self.checkAllSettings(not checked)

        for setting in settings:
            self._settings[setting].setChecked(checked)

    def toggledSettings(self) -> List[NovelSetting]:
        return [k for k, v in self._settings.items() if v.isChecked()]

    def _addSetting(self, setting: NovelSetting, row: int, col: int):
        toggle = NovelPanelCustomizationToggle(setting)
        self._settings[setting] = toggle
        toggle.toggled.connect(partial(self._settingToggled, setting))
        toggle.clicked.connect(partial(self._settingChanged, setting))
        toggle.installEventFilter(self)
        self._grid.addWidget(toggle, row, col, 1, 1)

    def _settingToggled(self, setting: NovelSetting, toggled: bool):
        self._novel.prefs.settings[setting.value] = toggled

    def _settingChanged(self, setting: NovelSetting, toggled: bool):
        self.clicked.emit(setting, toggled)


class NovelQuickPanelCustomizationWidget(NovelPanelSettingsWidget, EventListener):
    def __init__(self, parent=None):
        super().__init__(parent)

    @overrides
    def setNovel(self, novel: Novel):
        super().setNovel(novel)
        event_dispatchers.instance(self._novel).register(self, *panel_events)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, NovelPanelCustomizationEvent):
            self._settings[event.setting].setChecked(event.toggled)

    @overrides
    def _settingToggled(self, setting: NovelSetting, toggled: bool):
        pass

    @overrides
    def _settingChanged(self, setting: NovelSetting, toggled: bool):
        toggle_setting(self, self._novel, setting, toggled)


class NovelQuickPanelCustomizationButton(QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(IconRegistry.from_name('fa5s.cubes'))
        self.setToolTip('Customize what panels are visible')
        pointy(self)
        self.installEventFilter(ButtonPressResizeEventFilter(self))

        self._menu = MenuWidget(self)
        self._customizationWidget = NovelQuickPanelCustomizationWidget()
        apply_white_menu(self._menu)
        self._menu.addWidget(self._customizationWidget)

    def setNovel(self, novel: Novel):
        self._customizationWidget.setNovel(novel)

    # def reset(self):
    #     self._customizationWidget.reset()


class NovelSettingsWidget(QWidget, EventListener):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        vbox(self, spacing=10)
        self._settings: Dict[NovelSetting, NovelSettingToggle] = {}
        self._addSettingToggle(NovelSetting.Mindmap)
        self._addSettingToggle(NovelSetting.Structure)
        self._addSettingToggle(NovelSetting.Storylines)
        self._addSettingToggle(NovelSetting.Characters)
        wdgScenes = self._addSettingToggle(NovelSetting.Scenes)
        self._addSettingToggle(NovelSetting.Track_pov, wdgScenes)
        # wdgPov = NovelPovSettingWidget()
        # wdgScenes.addChild(wdgPov)
        self._addSettingToggle(NovelSetting.Track_emotion, wdgScenes)
        self._addSettingToggle(NovelSetting.Track_motivation, wdgScenes)
        self._addSettingToggle(NovelSetting.Track_conflict, wdgScenes)
        self._addSettingToggle(NovelSetting.World_building)
        self._addSettingToggle(NovelSetting.Documents)
        self._addSettingToggle(NovelSetting.Manuscript)
        self._addSettingToggle(NovelSetting.Management)
        self.layout().addWidget(vspacer())

        event_dispatchers.instance(self._novel).register(self, *panel_events)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, NovelPanelCustomizationEvent):
            self._settings[event.setting].setChecked(event.toggled)

    def _addSettingToggle(self, setting: NovelSetting,
                          parent: Optional[NovelSettingToggle] = None) -> NovelSettingToggle:
        toggle = NovelSettingToggle(self._novel, setting)
        toggle.settingToggled.connect(self._toggled)
        self._settings[setting] = toggle
        if parent:
            parent.addChild(toggle)
        else:
            self.layout().addWidget(toggle)

        return toggle

    def _toggled(self, setting: NovelSetting, toggled: bool):
        toggle_setting(self, self._novel, setting, toggled)
