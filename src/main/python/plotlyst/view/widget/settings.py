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
from typing import Dict, Optional

import qtanim
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QEvent
from PyQt6.QtGui import QIcon, QPalette, QColor
from PyQt6.QtWidgets import QWidget, QPushButton, QToolButton
from overrides import overrides
from qthandy import transparent, sp, vbox, hbox, vspacer, incr_font, pointy, grid
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR, PLOTLYST_TERTIARY_COLOR
from src.main.python.plotlyst.core.domain import Novel, NovelSetting
from src.main.python.plotlyst.view.common import label, ButtonPressResizeEventFilter
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.style.base import apply_white_menu
from src.main.python.plotlyst.view.widget.input import Toggle

setting_titles: Dict[NovelSetting, str] = {
    NovelSetting.Structure: 'Story structure',
    NovelSetting.Mindmap: 'Events map',
    NovelSetting.Storylines: 'Storylines',
    NovelSetting.Characters: 'Characters',
    NovelSetting.Scenes: 'Scenes',
    NovelSetting.World_building: 'World-building',
    NovelSetting.Manuscript: 'Manuscript',
    NovelSetting.Documents: 'Documents',
    NovelSetting.Management: 'Task management',
}
setting_descriptions: Dict[NovelSetting, str] = {
    NovelSetting.Structure: "Follow a story structure to help you with your story's pacing and escalation",
    NovelSetting.Mindmap: "Visualize your story's events in a mindmap. Ideal for brainstorming or any other stage in writing",
    NovelSetting.Storylines: "Create separate storylines for plot, character's change, subplots, or relationship plots",
    NovelSetting.Characters: "Create a cast of characters with different roles, personalities, backstories, goals, and relationships among them",
    NovelSetting.Scenes: "Create scene cards for early outlining or later revision purposes to have characters, conflicts, or storylines associated to the scenes",
    NovelSetting.World_building: "[BETA] Develop your story's world by creating fictional settings and lore",
    NovelSetting.Manuscript: "Write your story in Plotlyst using the manuscript panel",
    NovelSetting.Documents: "Add documents for your planning or research",
    NovelSetting.Management: "Stay organized by tracking your tasks in a simple Kanban board",
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
    elif setting == NovelSetting.World_building:
        return IconRegistry.world_building_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Manuscript:
        return IconRegistry.manuscript_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Documents:
        return IconRegistry.document_edition_icon(color=color, color_on=color_on)
    elif setting == NovelSetting.Management:
        return IconRegistry.board_icon(color, color_on)
    return QIcon()


class NovelSettingToggle(QWidget):
    settingToggled = pyqtSignal(NovelSetting, bool)

    def __init__(self, novel: Novel, setting: NovelSetting, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._setting = setting

        self._title = QPushButton()
        self._title.setText(setting_titles[setting])
        self._title.setIcon(setting_icon(setting))
        palette = self._title.palette()
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, QColor(PLOTLYST_SECONDARY_COLOR))
        self._title.setPalette(palette)
        transparent(self._title)
        incr_font(self._title, 2)

        self._description = label(setting_descriptions[setting], description=True)
        self._description.setWordWrap(True)
        sp(self._description).h_exp()

        self._toggle = Toggle()
        self._toggle.setChecked(True)
        self._toggle.toggled.connect(self._toggled)

        self._wdgTitle = QWidget()
        vbox(self._wdgTitle)
        self._wdgTitle.layout().addWidget(self._title, alignment=Qt.AlignmentFlag.AlignLeft)
        self._wdgTitle.layout().addWidget(self._description)

        self._wdgHeader = QWidget()
        self._wdgHeader.setObjectName('wdgHeader')
        hbox(self._wdgHeader)
        self._wdgHeader.layout().addWidget(self._wdgTitle)
        self._wdgHeader.layout().addWidget(self._toggle, alignment=Qt.AlignmentFlag.AlignTop)

        hbox(self, 0, 0)
        self.layout().addWidget(self._wdgHeader)

    def _toggled(self, toggled: bool):
        self._wdgTitle.setEnabled(toggled)
        self.settingToggled.emit(self._setting, toggled)


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


class NovelQuickPanelCustomizationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel: Optional[Novel] = None
        self.setProperty('relaxed-white-bg', True)

        vbox(self)
        self._wdgCenter = QWidget()
        self._wdgBottom = QWidget()
        self._lblDesc = label('', wordWrap=True, description=True)
        self._lblDesc.setMinimumSize(400, 100)
        self._lblDesc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox(self._wdgBottom, margin=15).addWidget(self._lblDesc, alignment=Qt.AlignmentFlag.AlignCenter)

        self.layout().addWidget(label('Customize your experience:'),
                                alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._wdgCenter)
        self.layout().addWidget(self._wdgBottom)
        self._grid = grid(self._wdgCenter)

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

    def reset(self):
        self._novel = None

    @overrides
    def eventFilter(self, watched: 'QObject', event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            self._lblDesc.setText(setting_descriptions[watched.setting()])
        return super().eventFilter(watched, event)

    def _addSetting(self, setting: NovelSetting, row: int, col: int):
        toggle = NovelPanelCustomizationToggle(setting)
        toggle.clicked.connect(partial(self._settingChanged, setting))
        toggle.installEventFilter(self)
        self._grid.addWidget(toggle, row, col, 1, 1)

    def _settingChanged(self, setting: NovelSetting, toggled: bool):
        pass


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

    def reset(self):
        self._customizationWidget.reset()


class NovelSettingsWidget(QWidget):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        vbox(self, spacing=10)
        self.layout().addWidget(NovelSettingToggle(self._novel, NovelSetting.Mindmap))
        self.layout().addWidget(NovelSettingToggle(self._novel, NovelSetting.Structure))
        self.layout().addWidget(NovelSettingToggle(self._novel, NovelSetting.Storylines))
        self.layout().addWidget(NovelSettingToggle(self._novel, NovelSetting.Characters))
        self.layout().addWidget(NovelSettingToggle(self._novel, NovelSetting.Scenes))
        self.layout().addWidget(NovelSettingToggle(self._novel, NovelSetting.World_building))
        self.layout().addWidget(NovelSettingToggle(self._novel, NovelSetting.Documents))
        self.layout().addWidget(NovelSettingToggle(self._novel, NovelSetting.Manuscript))
        self.layout().addWidget(NovelSettingToggle(self._novel, NovelSetting.Management))
        self.layout().addWidget(vspacer())
