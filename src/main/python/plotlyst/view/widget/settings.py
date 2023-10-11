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
from typing import Dict

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QPalette, QColor
from PyQt6.QtWidgets import QWidget, QPushButton
from qthandy import transparent, sp, vbox, hbox, vspacer, incr_font

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel, NovelSetting
from src.main.python.plotlyst.view.common import label
from src.main.python.plotlyst.view.icons import IconRegistry
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


def setting_icon(setting: NovelSetting) -> QIcon:
    if setting == NovelSetting.Structure:
        return IconRegistry.story_structure_icon(color=PLOTLYST_SECONDARY_COLOR)
    elif setting == NovelSetting.Mindmap:
        return IconRegistry.from_name('ri.mind-map', PLOTLYST_SECONDARY_COLOR)
    elif setting == NovelSetting.Storylines:
        return IconRegistry.storylines_icon(color=PLOTLYST_SECONDARY_COLOR)
    elif setting == NovelSetting.Characters:
        return IconRegistry.character_icon(color=PLOTLYST_SECONDARY_COLOR)
    elif setting == NovelSetting.Scenes:
        return IconRegistry.scene_icon(color=PLOTLYST_SECONDARY_COLOR)
    elif setting == NovelSetting.World_building:
        return IconRegistry.world_building_icon(color=PLOTLYST_SECONDARY_COLOR)
    elif setting == NovelSetting.Manuscript:
        return IconRegistry.manuscript_icon(color=PLOTLYST_SECONDARY_COLOR)
    elif setting == NovelSetting.Documents:
        return IconRegistry.document_edition_icon(color=PLOTLYST_SECONDARY_COLOR)
    elif setting == NovelSetting.Management:
        return IconRegistry.board_icon()
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

    # @overrides
    # def enterEvent(self, event: QEnterEvent) -> None:
    #     self._toggle.setVisible(True)
    #
    # @overrides
    # def leaveEvent(self, a0: QEvent) -> None:
    #     self._toggle.setVisible(False)

    def _toggled(self, toggled: bool):
        self._wdgTitle.setEnabled(toggled)
        self.settingToggled.emit(self._setting, toggled)


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
