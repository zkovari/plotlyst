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

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget
from qthandy import line

from plotlyst.core.domain import Novel, NovelSetting
from plotlyst.view.common import wrap
from plotlyst.view.generated.characters_view_preferences_widget_ui import Ui_CharactersViewPreferences
from plotlyst.view.icons import IconRegistry


class CharactersPreferencesWidget(QWidget, Ui_CharactersViewPreferences):
    settingToggled = pyqtSignal(NovelSetting, bool)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.novel = novel

        self.tabTable.layout().insertWidget(1, line(color='lightgrey'))
        self.tabTable.layout().insertWidget(7, wrap(line(color='lightgrey'), margin_left=20))

        self.btnTableRole.setIcon(IconRegistry.from_name('fa5s.chess-bishop'))
        self.btnTableAge.setIcon(IconRegistry.from_name('fa5s.birthday-cake'))
        self.btnTableGender.setIcon(IconRegistry.from_name('mdi.gender-female'))
        self.btnTableOccupation.setIcon(IconRegistry.from_name('fa5s.briefcase'))

        self.btnTableEnneagram.setIcon(IconRegistry.from_name('mdi.numeric-9-circle'))
        self.btnTableMbti.setIcon(IconRegistry.from_name('mdi.head-question-outline'))

        self.cbTableRole.setChecked(self.novel.prefs.toggled(NovelSetting.CHARACTER_TABLE_ROLE))
        self.cbTableAge.setChecked(self.novel.prefs.toggled(NovelSetting.CHARACTER_TABLE_AGE, False))
        self.cbTableGender.setChecked(self.novel.prefs.toggled(NovelSetting.CHARACTER_TABLE_GENDER, False))
        self.cbTableOccupation.setChecked(self.novel.prefs.toggled(NovelSetting.CHARACTER_TABLE_OCCUPATION, False))
        self.cbTableEnneagram.setChecked(self.novel.prefs.toggled(NovelSetting.CHARACTER_TABLE_ENNEAGRAM))
        self.cbTableMbti.setChecked(self.novel.prefs.toggled(NovelSetting.CHARACTER_TABLE_MBTI))

        self.cbTableRole.clicked.connect(partial(self.settingToggled.emit, NovelSetting.CHARACTER_TABLE_ROLE))
        self.cbTableAge.clicked.connect(partial(self.settingToggled.emit, NovelSetting.CHARACTER_TABLE_AGE))
        self.cbTableGender.clicked.connect(partial(self.settingToggled.emit, NovelSetting.CHARACTER_TABLE_GENDER))
        self.cbTableOccupation.clicked.connect(
            partial(self.settingToggled.emit, NovelSetting.CHARACTER_TABLE_OCCUPATION))
        self.cbTableEnneagram.clicked.connect(partial(self.settingToggled.emit, NovelSetting.CHARACTER_TABLE_ENNEAGRAM))
        self.cbTableMbti.clicked.connect(partial(self.settingToggled.emit, NovelSetting.CHARACTER_TABLE_MBTI))
