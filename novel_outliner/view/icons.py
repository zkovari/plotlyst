from typing import Dict

import qtawesome
from PyQt5.QtGui import QIcon, QPixmap

from novel_outliner.core.domain import Character
from novel_outliner.view.common import rounded_pixmap


class IconRegistry:

    @staticmethod
    def ok_icon() -> QIcon:
        return qtawesome.icon('ei.ok', color='green')

    @staticmethod
    def wrong_icon() -> QIcon:
        return qtawesome.icon('ei.remove', color='red')

    @staticmethod
    def error_icon() -> QIcon:
        return qtawesome.icon('fa5s.exclamation-triangle', color='red')

    @staticmethod
    def circle_icon() -> QIcon:
        return qtawesome.icon('mdi.circle-slice-8', color='green')

    @staticmethod
    def stop_icon() -> QIcon:
        return qtawesome.icon('ei.stop-alt', color='red')

    @staticmethod
    def warning_icon() -> QIcon:
        return qtawesome.icon('fa.warning')

    @staticmethod
    def empty_icon() -> QIcon:
        return QIcon('')

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
    def arrow_down_thin_icon() -> QIcon:
        return qtawesome.icon('fa5s.arrow-down')

    @staticmethod
    def arrow_down_thick_icon() -> QIcon:
        return qtawesome.icon('ei.arrow-down')

    @staticmethod
    def arrow_up_thick_icon() -> QIcon:
        return qtawesome.icon('ei.arrow-up')

    @staticmethod
    def toggle_off_icon() -> QIcon:
        return qtawesome.icon('fa5s.toggle-off')

    @staticmethod
    def toggle_on_icon() -> QIcon:
        return qtawesome.icon('fa5s.toggle-on', color='#3532a1')

    @staticmethod
    def info_icon() -> QIcon:
        return qtawesome.icon('fa5s.info', color='darkblue')

    @staticmethod
    def tree_icon() -> QIcon:
        return qtawesome.icon('mdi.file-tree-outline')

    @staticmethod
    def plus_icon() -> QIcon:
        return qtawesome.icon('fa5s.plus', color='green')

    @staticmethod
    def minus_icon() -> QIcon:
        return qtawesome.icon('fa5s.minus', color='red')

    @staticmethod
    def history_icon() -> QIcon:
        return qtawesome.icon('fa5s.history')

    @staticmethod
    def character_icon() -> QIcon:
        return qtawesome.icon('fa5s.user')

    @staticmethod
    def location_icon() -> QIcon:
        return qtawesome.icon('fa5s.location-arrow')

    @staticmethod
    def scene_icon() -> QIcon:
        return qtawesome.icon('mdi.movie-open')

    @staticmethod
    def book_icon() -> QIcon:
        return qtawesome.icon('fa5s.book-open')

    @staticmethod
    def synopsis_icon() -> QIcon:
        return qtawesome.icon('mdi.file-document')

    @staticmethod
    def general_info_icon() -> QIcon:
        return qtawesome.icon('mdi.information-outline')

    @staticmethod
    def custom_scene_icon() -> QIcon:
        return qtawesome.icon('fa5s.yin-yang', color='magenta')

    @staticmethod
    def action_scene_icon() -> QIcon:
        return qtawesome.icon('fa5s.yin-yang', color='red')

    @staticmethod
    def reaction_scene_icon() -> QIcon:
        return qtawesome.icon('fa5s.yin-yang', color='darkblue')

    @staticmethod
    def hashtag_icon() -> QIcon:
        return qtawesome.icon('fa5s.hashtag')

    @staticmethod
    def graph_icon() -> QIcon:
        return qtawesome.icon('ei.graph')

    @staticmethod
    def wip_icon() -> QIcon:
        return qtawesome.icon('mdi.progress-question')

    @staticmethod
    def tasks_icon() -> QIcon:
        return qtawesome.icon('fa5s.tasks')

    @staticmethod
    def timeline_icon() -> QIcon:
        return qtawesome.icon('mdi.chart-timeline-variant')

    @staticmethod
    def reports_icon() -> QIcon:
        return qtawesome.icon('fa5.chart-bar')

    @staticmethod
    def notes_icon() -> QIcon:
        return qtawesome.icon('mdi.notebook')


class AvatarsRegistry:
    def __init__(self):
        self._avatars: Dict[int, QPixmap] = {}

    def pixmap(self, character: Character) -> QPixmap:
        if character.id not in self._avatars:
            array = character.avatar
            pixmap = QPixmap()
            if array:
                pixmap.loadFromData(array)
            self._avatars[character.id] = rounded_pixmap(pixmap)

        return self._avatars[character.id]


avatars = AvatarsRegistry()
