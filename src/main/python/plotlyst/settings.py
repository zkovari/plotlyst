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
from typing import Optional, List, Dict

from PyQt6.QtCore import QCoreApplication, QSettings


class AppSettings:
    WORKSPACE = 'workspace'
    LAUNCHED_BEFORE = 'launchedBefore'
    LAST_NOVEL_ID = 'lastNovelId'

    def __init__(self):
        self._settings: QSettings = QSettings()

    def init_org(self):
        QCoreApplication.setOrganizationName('Plotlyst')
        QCoreApplication.setOrganizationDomain('plotlyst.com')
        QCoreApplication.setApplicationName('Plotlyst')
        self._settings = QSettings()

    def clear(self):
        self._settings.clear()

    def workspace(self) -> Optional[str]:
        return self._settings.value(self.WORKSPACE)

    def set_workspace(self, value: str):
        self._settings.setValue(self.WORKSPACE, value)

    def first_launch(self) -> bool:
        return not self._settings.value(self.LAUNCHED_BEFORE, False)

    def set_launched_before(self):
        self._settings.setValue(self.LAUNCHED_BEFORE, True)

    def last_novel_id(self) -> Optional[int]:
        return self._settings.value(self.LAST_NOVEL_ID)

    def set_last_novel_id(self, value: int):
        self._settings.setValue(self.LAST_NOVEL_ID, value)

    def hint_showed(self, hint_id: str) -> bool:
        return self._settings.value(hint_id) == 'true'

    def set_hint_showed(self, hint_id: str):
        self._settings.setValue(hint_id, 'true')

    def reset_hint_showed(self, hint_id: str):
        self._settings.remove(hint_id)


settings = AppSettings()

STORY_LINE_COLOR_CODES: Dict[str, List[str]] = {
    'main': [
        '#03396c',  # yale blue
        '#338740',  # sea green
        '#cc3363',  # dogwood rose
        '#b388eb',  # lavender
        '#6d597a',  # chinese violate
        '#FAAE4A',  # princeton orange
        '#F50574',  # rose
    ],
    'internal': [
        '#0FADBB',  # moonstone
        '#e8c2ca',  # fairy tale
        '#fcd5ce',  # pale dogwood
    ],
    'subplot': [
        '#d4a373',  # buff
        '#b7b7a4',  # ash grey
        '#D48172',  # coral pink
        '#93a8ac',  # cadet grey
    ],

}

CHARACTER_INITIAL_AVATAR_COLOR_CODES: List[str] = [
    '#03396c',
    '#0e9aa7',
    '#62c370',
    '#cc3363',
    '#f5e960',
    '#3c4f76',
    '#b388eb',
    '#8093f1',
]
