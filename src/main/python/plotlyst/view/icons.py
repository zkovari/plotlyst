"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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

import qtawesome
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QPixmap

from src.main.python.plotlyst.core.domain import Character, VERY_UNHAPPY, UNHAPPY, HAPPY, VERY_HAPPY
from src.main.python.plotlyst.settings import CHARACTER_INITIAL_AVATAR_COLOR_CODES
from src.main.python.plotlyst.view.common import rounded_pixmap


class IconRegistry:

    @staticmethod
    def ok_icon() -> QIcon:
        return qtawesome.icon('ei.ok', color='green')

    @staticmethod
    def wrong_icon() -> QIcon:
        return qtawesome.icon('ei.remove', color='red')

    @staticmethod
    def cancel_icon() -> QIcon:
        return qtawesome.icon('mdi.backspace', color='red')

    @staticmethod
    def error_icon() -> QIcon:
        return qtawesome.icon('fa5s.exclamation-triangle', color='red')

    @staticmethod
    def empty_icon() -> QIcon:
        return QIcon('')

    # used to fill up space in models
    @staticmethod
    def invisible_white_icon():
        return qtawesome.icon('fa5.circle', color='white')

    @staticmethod
    def copy_icon() -> QIcon:
        return qtawesome.icon('fa5.copy')

    @staticmethod
    def filter_icon() -> QIcon:
        return qtawesome.icon('fa5s.filter')

    @staticmethod
    def edit_icon() -> QIcon:
        return qtawesome.icon('mdi.pencil')

    @staticmethod
    def plus_icon(color: str = 'green') -> QIcon:
        return qtawesome.icon('fa5s.plus', color=color)

    @staticmethod
    def minus_icon() -> QIcon:
        return qtawesome.icon('fa5s.minus', color='red')

    @staticmethod
    def history_icon() -> QIcon:
        return qtawesome.icon('fa5s.history')

    @staticmethod
    def character_icon() -> QIcon:
        return qtawesome.icon('fa5s.user', color_on='darkBlue')

    @staticmethod
    def location_icon() -> QIcon:
        return qtawesome.icon('fa5s.location-arrow')

    @staticmethod
    def scene_icon() -> QIcon:
        return qtawesome.icon('mdi.movie-open', color_on='darkBlue')

    @staticmethod
    def chapter_icon() -> QIcon:
        return qtawesome.icon('ei.book')

    @staticmethod
    def book_icon() -> QIcon:
        return qtawesome.icon('fa5s.book-open', color_on='darkBlue')

    @staticmethod
    def synopsis_icon() -> QIcon:
        return qtawesome.icon('mdi.file-document')

    @staticmethod
    def general_info_icon() -> QIcon:
        return qtawesome.icon('mdi.information-outline')

    @staticmethod
    def custom_scene_icon() -> QIcon:
        return qtawesome.icon('fa5s.yin-yang', color='#c0c2ce')

    @staticmethod
    def action_scene_icon() -> QIcon:
        return qtawesome.icon('fa5s.yin-yang', color='#fe4a49')

    @staticmethod
    def reaction_scene_icon() -> QIcon:
        return qtawesome.icon('fa5s.yin-yang', color='#4b86b4')

    @staticmethod
    def hashtag_icon() -> QIcon:
        return qtawesome.icon('fa5s.hashtag')

    @staticmethod
    def graph_icon() -> QIcon:
        return qtawesome.icon('ei.graph')

    @staticmethod
    def wip_icon() -> QIcon:
        return qtawesome.icon('mdi.progress-question', options=[{'scale_factor': 1.2}])

    @staticmethod
    def tasks_icon() -> QIcon:
        return qtawesome.icon('fa5s.tasks')

    @staticmethod
    def timeline_icon() -> QIcon:
        return qtawesome.icon('mdi.chart-timeline-variant', color_on='darkBlue')

    @staticmethod
    def reports_icon() -> QIcon:
        return qtawesome.icon('fa5.chart-bar', color_on='darkBlue')

    @staticmethod
    def notes_icon() -> QIcon:
        return qtawesome.icon('mdi.notebook', color_on='darkBlue')

    @staticmethod
    def act_one_icon() -> QIcon:
        return qtawesome.icon('mdi.numeric-1-circle', color='#02bcd4')

    @staticmethod
    def act_two_icon() -> QIcon:
        return qtawesome.icon('mdi.numeric-2-circle', color='#1bbc9c')

    @staticmethod
    def act_three_icon() -> QIcon:
        return qtawesome.icon('mdi.numeric-3-circle', color='#ff7800')

    @staticmethod
    def table_icon() -> QIcon:
        return qtawesome.icon('fa.list-alt')

    @staticmethod
    def goal_icon() -> QIcon:
        return qtawesome.icon('mdi.target', color='darkBlue')

    @staticmethod
    def decision_icon() -> QIcon:
        return qtawesome.icon('fa.lightbulb-o', color='darkGreen')

    @staticmethod
    def reaction_icon() -> QIcon:
        return qtawesome.icon('fa.shield')

    @staticmethod
    def disaster_icon() -> QIcon:
        return qtawesome.icon('fa.bomb', color='red')

    @staticmethod
    def dilemma_icon() -> QIcon:
        return qtawesome.icon('fa.question-circle-o')

    @staticmethod
    def conflict_icon(color: str = 'orange') -> QIcon:
        return qtawesome.icon('mdi.sword-cross', color=color)

    @staticmethod
    def home_icon() -> QIcon:
        return qtawesome.icon('fa5s.home', color_on='darkBlue')

    @staticmethod
    def trash_can_icon(color: str = 'red') -> QIcon:
        return qtawesome.icon('fa5s.trash-alt', color=color)

    @staticmethod
    def arrow_right_thick_icon() -> QIcon:
        return qtawesome.icon('ei.arrow-right')

    @staticmethod
    def arrow_left_thick_icon() -> QIcon:
        return qtawesome.icon('ei.arrow-left')

    @staticmethod
    def return_icon() -> QIcon:
        return qtawesome.icon('ei.return-key')

    @staticmethod
    def eye_open_icon() -> QIcon:
        return qtawesome.icon('fa5.eye')

    @staticmethod
    def eye_closed_icon() -> QIcon:
        return qtawesome.icon('fa5.eye-slash')

    @staticmethod
    def emotion_icon_from_feeling(feeling: int) -> QIcon:
        if feeling == VERY_UNHAPPY:
            return qtawesome.icon('fa5s.sad-cry', color='red')
        if feeling == UNHAPPY:
            return qtawesome.icon('mdi.emoticon-sad', color='orange')
        if feeling == HAPPY:
            return qtawesome.icon('fa5s.smile', color='lightgreen')
        if feeling == VERY_HAPPY:
            return qtawesome.icon('fa5s.smile-beam', color='darkgreen')

        return qtawesome.icon('mdi.emoticon-neutral', color='grey')

    @staticmethod
    def upload_icon() -> QIcon:
        return qtawesome.icon('fa5s.file-upload')

    @staticmethod
    def portrait_icon() -> QIcon:
        return qtawesome.icon('fa5s.portrait')


class AvatarsRegistry:
    def __init__(self):
        self._avatars: Dict[int, QPixmap] = {}

    def pixmap(self, character: Character) -> QPixmap:
        if character.id not in self._avatars:
            if character.avatar:
                array = character.avatar
                pixmap = QPixmap()
                if array:
                    pixmap.loadFromData(array)
                self._avatars[character.id] = rounded_pixmap(pixmap)
            else:
                _sum = sum([ord(x) for x in character.name])
                color = CHARACTER_INITIAL_AVATAR_COLOR_CODES[_sum % len(CHARACTER_INITIAL_AVATAR_COLOR_CODES)]
                icon: QIcon = qtawesome.icon(f'mdi.alpha-{character.name[0].lower()}-circle-outline',
                                             options=[{'scale_factor': 1.2}], color=color)
                self._avatars[character.id] = icon.pixmap(QSize(64, 64))

        return self._avatars[character.id]

    def update(self, character: Character):
        if character.id in self._avatars.keys():
            self._avatars.pop(character.id)
        self.pixmap(character)


avatars = AvatarsRegistry()
