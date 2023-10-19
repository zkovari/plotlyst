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
from typing import Dict, Optional

import qtawesome
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QLabel

from src.main.python.plotlyst.common import ACT_ONE_COLOR, ACT_TWO_COLOR, ACT_THREE_COLOR, CONFLICT_CHARACTER_COLOR, \
    CONFLICT_SOCIETY_COLOR, CONFLICT_NATURE_COLOR, CONFLICT_TECHNOLOGY_COLOR, CONFLICT_SUPERNATURAL_COLOR, \
    CONFLICT_SELF_COLOR, CHARACTER_MAJOR_COLOR, CHARACTER_MINOR_COLOR, CHARACTER_SECONDARY_COLOR, \
    PLOTLYST_SECONDARY_COLOR, PLOTLYST_MAIN_COLOR
from src.main.python.plotlyst.core.domain import Character, VERY_UNHAPPY, UNHAPPY, HAPPY, VERY_HAPPY, ConflictType, \
    Scene, PlotType, MALE, FEMALE, TRANSGENDER, NON_BINARY, GENDERLESS, ScenePurposeType
from src.main.python.plotlyst.core.template import SelectionItem
from src.main.python.plotlyst.settings import CHARACTER_INITIAL_AVATAR_COLOR_CODES
from src.main.python.plotlyst.view.common import rounded_pixmap


class IconRegistry:

    @staticmethod
    def ok_icon(color: str = 'green') -> QIcon:
        return qtawesome.icon('ei.ok', color=color)

    @staticmethod
    def wrong_icon(color: str = 'red') -> QIcon:
        return qtawesome.icon('ei.remove', color=color)

    @staticmethod
    def close_icon(color: str = 'black') -> QIcon:
        return qtawesome.icon('ei.remove', color=color)

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
    def copy_icon(color_on: str = 'black') -> QIcon:
        return qtawesome.icon('fa5.copy', color_on=color_on)

    @staticmethod
    def paste_icon() -> QIcon:
        return qtawesome.icon('fa5s.paste')

    @staticmethod
    def cut_icon() -> QIcon:
        return qtawesome.icon('fa5s.cut')

    @staticmethod
    def increase_font_size_icon() -> QIcon:
        return IconRegistry.from_name('mdi.format-font-size-increase')

    @staticmethod
    def decrease_font_size_icon() -> QIcon:
        return IconRegistry.from_name('mdi.format-font-size-decrease')

    @staticmethod
    def filter_icon() -> QIcon:
        return qtawesome.icon('fa5s.filter')

    @staticmethod
    def preferences_icon() -> QIcon:
        return qtawesome.icon('fa5s.sliders-h')

    @staticmethod
    def edit_icon(color: str = 'black', color_on: str = 'black') -> QIcon:
        return IconRegistry.from_name('mdi.pencil', color, color_on=color_on)

    @staticmethod
    def plus_edit_icon(color: str = '#004385') -> QIcon:
        return IconRegistry.from_name('mdi.pencil-plus', color=color)

    @staticmethod
    def plus_icon(color: str = 'green') -> QIcon:
        return qtawesome.icon('fa5s.plus', color=color)

    @staticmethod
    def plus_circle_icon(color: str = 'black') -> QIcon:
        return qtawesome.icon('ei.plus-sign', color=color)

    @staticmethod
    def minus_icon(color: str = 'red') -> QIcon:
        return qtawesome.icon('fa5s.minus', color=color)

    @staticmethod
    def history_icon() -> QIcon:
        return qtawesome.icon('fa5s.history')

    @staticmethod
    def tutorial_icon() -> QIcon:
        return IconRegistry.from_name('mdi6.school')

    @staticmethod
    def character_icon(color: str = 'black', color_on: str = PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return qtawesome.icon('fa5s.user', color=color, color_on=color_on)

    @staticmethod
    def major_character_icon() -> QIcon:
        return IconRegistry.from_name('mdi6.chess-king', CHARACTER_MAJOR_COLOR)

    @staticmethod
    def secondary_character_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.chess-knight', CHARACTER_SECONDARY_COLOR)

    @staticmethod
    def minor_character_icon() -> QIcon:
        return IconRegistry.from_name('mdi.chess-pawn', CHARACTER_MINOR_COLOR)

    @staticmethod
    def location_icon(color: str = 'black') -> QIcon:
        return qtawesome.icon('fa5s.map-pin', color=color, color_on='darkBlue', options=[{'scale_factor': 1.1}])

    @staticmethod
    def world_building_icon(color: str = 'black', color_on: str = PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi.globe-model', color=color, color_on=color_on)

    @staticmethod
    def board_icon(color: str = 'black', color_on: str = PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi6.clipboard-check-outline', color=color, color_on=color_on)

    @staticmethod
    def scene_icon(color: str = 'black', color_on: str = PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi.movie-open', color, color_on=color_on, scale=1.1)

    @staticmethod
    def manuscript_icon(color: str = 'black', color_on: str = PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return IconRegistry.from_name('fa5s.scroll', color=color, color_on=color_on)

    @staticmethod
    def chapter_icon() -> QIcon:
        return IconRegistry.from_name('ei.book')

    @staticmethod
    def prologue_icon() -> QIcon:
        # color='#669bbc'
        return IconRegistry.from_name('mdi.alpha-p-box-outline')

    @staticmethod
    def epilogue_icon() -> QIcon:
        # color='#e76f51'
        return IconRegistry.from_name('mdi.alpha-e-box-outline')

    @staticmethod
    def interlude_icon() -> QIcon:
        return IconRegistry.from_name('mdi.information-variant')

    @staticmethod
    def book_icon(color='black', color_on=PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return qtawesome.icon('fa5s.book-open', color_on=color_on, color=color)

    @staticmethod
    def synopsis_icon(**kwargs) -> QIcon:
        return IconRegistry.from_name('mdi.file-document', **kwargs)

    @staticmethod
    def general_info_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.info-circle', color=PLOTLYST_SECONDARY_COLOR)

    @staticmethod
    def action_scene_icon(resolved: bool = False, trade_off: bool = False) -> QIcon:
        if resolved:
            color = '#0b6e4f'
        elif trade_off:
            color = '#832161'
        else:
            color = '#fe4a49'
        return qtawesome.icon('fa5s.circle', 'fa5s.yin-yang',
                              options=[{'color': 'white', 'scale_factor': 1},
                                       {'color': color, 'color_disabled': 'black'}])

    @staticmethod
    def scene_type_icon(scene: Scene) -> Optional[QIcon]:
        if scene.purpose == ScenePurposeType.Story:
            return IconRegistry.action_scene_icon(scene.outcome_resolution(), scene.outcome_trade_off())
        elif scene.purpose == ScenePurposeType.Reaction:
            return IconRegistry.reaction_scene_icon()
        elif scene.purpose == ScenePurposeType.Character:
            return IconRegistry.character_development_scene_icon()
        elif scene.purpose == ScenePurposeType.Emotion:
            return IconRegistry.emotion_scene_icon()
        elif scene.purpose == ScenePurposeType.Setup:
            return IconRegistry.setup_scene_icon()
        elif scene.purpose == ScenePurposeType.Exposition:
            return IconRegistry.exposition_scene_icon()
        else:
            return IconRegistry.empty_icon()

    @staticmethod
    def reaction_scene_icon() -> QIcon:
        return qtawesome.icon('fa5s.circle', 'fa5s.yin-yang',
                              options=[{'color': 'white', 'scale_factor': 1},
                                       {'color': '#4b86b4', 'color_disabled': 'black'}])

    @staticmethod
    def happening_scene_icon() -> QIcon:
        return IconRegistry.from_name('mdi.motion-outline', 'grey', 'black')

    @staticmethod
    def setup_scene_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.seedling', 'grey')

    @staticmethod
    def exposition_scene_icon() -> QIcon:
        return IconRegistry.from_name('mdi.information-outline', 'grey', 'black')

    @staticmethod
    def character_development_scene_icon() -> QIcon:
        return IconRegistry.from_name('mdi.account-cog', 'grey', 'black')

    @staticmethod
    def emotion_scene_icon() -> QIcon:
        return IconRegistry.from_name('mdi.emoticon-outline', 'grey', 'black')

    @staticmethod
    def summary_scene_icon() -> QIcon:
        return IconRegistry.from_name('ei.list-alt', 'grey', 'black')

    @staticmethod
    def hashtag_icon(color: str = 'black') -> QIcon:
        return IconRegistry.from_name('fa5s.hashtag', color)

    @staticmethod
    def tag_plus_icon() -> QIcon:
        return IconRegistry.from_name('mdi.tag-plus')

    @staticmethod
    def tags_icon(**kwargs) -> QIcon:
        return IconRegistry.from_name('ei.tags', **kwargs)

    @staticmethod
    def graph_icon() -> QIcon:
        return IconRegistry.from_name('ei.graph')

    @staticmethod
    def wip_icon() -> QIcon:
        return IconRegistry.from_name('mdi.progress-question')

    @staticmethod
    def tasks_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.tasks')

    @staticmethod
    def reports_icon(color: str = 'black', color_on: str = PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi.chart-arc', color=color, color_on=color_on, scale=1.4)

    @staticmethod
    def document_edition_icon(color: str = 'black', color_on=PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi.file-document-outline', color=color, color_on=color_on)

    @staticmethod
    def act_one_icon(color=ACT_ONE_COLOR, color_on=ACT_ONE_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi.numeric-1-circle', color=color, color_on=color_on)

    @staticmethod
    def act_two_icon(color=ACT_TWO_COLOR, color_on=ACT_TWO_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi.numeric-2-circle', color=color, color_on=color_on)

    @staticmethod
    def act_three_icon(color=ACT_THREE_COLOR, color_on=ACT_THREE_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi.numeric-3-circle', color=color, color_on=color_on)

    @staticmethod
    def table_icon() -> QIcon:
        return qtawesome.icon('fa5.list-alt', color_on=PLOTLYST_SECONDARY_COLOR)

    @staticmethod
    def goal_icon(color: str = 'darkBlue', color_on: str = 'darkBlue') -> QIcon:
        return IconRegistry.from_name('mdi.target', color=color, color_on=color_on)

    @staticmethod
    def decision_icon(color: str = '#219ebc', color_on='darkBlue') -> QIcon:
        return IconRegistry.from_name('fa5.lightbulb', color=color, color_on=color_on)

    @staticmethod
    def reaction_icon() -> QIcon:
        return qtawesome.icon('fa5s.shield-alt')

    @staticmethod
    def emotion_icon() -> QIcon:
        return IconRegistry.from_name('ri.emotion-sad-line')

    @staticmethod
    def disaster_icon(color: str = '#f4442e', color_on: str = '#f4442e') -> QIcon:
        return qtawesome.icon('fa5s.bomb', color=color, color_on=color_on)

    @staticmethod
    def dilemma_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.map-signs', '#ba6f4d')

    @staticmethod
    def conflict_icon(color: str = '#f3a712', color_on: str = '#f3a712') -> QIcon:
        return IconRegistry.from_name('mdi.sword-cross', color=color, color_on=color_on)

    @staticmethod
    def success_icon(color: str = '#0b6e4f', color_on: str = '#0b6e4f') -> QIcon:
        return IconRegistry.from_name('mdi.bullseye-arrow', color=color, color_on=color_on)

    @staticmethod
    def tradeoff_icon(color: str = '#832161', color_on: str = '#832161') -> QIcon:
        return IconRegistry.from_name('fa5s.balance-scale-left', color=color, color_on=color_on)

    @staticmethod
    def home_icon(color_on: str = 'darkBlue') -> QIcon:
        return IconRegistry.from_name('fa5s.home', color_on=color_on)

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
    def return_icon(color: str = PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return IconRegistry.from_name('fa5s.chevron-circle-left', color=color)

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
    def upload_icon(**kwargs) -> QIcon:
        return qtawesome.icon('fa5s.file-upload', **kwargs)

    @staticmethod
    def portrait_icon() -> QIcon:
        return qtawesome.icon('fa5s.portrait')

    @staticmethod
    def progress_check_icon(color: str = 'darkBlue', color_on=PLOTLYST_SECONDARY_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi.progress-check', color=color, color_on=color_on)

    @staticmethod
    def customization_icon() -> QIcon:
        return qtawesome.icon('fa5s.sliders-h')

    @staticmethod
    def restore_alert_icon(color='black') -> QIcon:
        return IconRegistry.from_name('mdi.restore-alert', color=color)

    @staticmethod
    def cards_icon() -> QIcon:
        return IconRegistry.from_name('mdi.cards', color_on=PLOTLYST_SECONDARY_COLOR)

    @staticmethod
    def conflict_type_icon(type: ConflictType) -> QIcon:
        if type == ConflictType.CHARACTER:
            return IconRegistry.conflict_character_icon()
        elif type == ConflictType.SOCIETY:
            return IconRegistry.conflict_society_icon()
        elif type == ConflictType.NATURE:
            return IconRegistry.conflict_nature_icon()
        elif type == ConflictType.TECHNOLOGY:
            return IconRegistry.conflict_technology_icon()
        elif type == ConflictType.SUPERNATURAL:
            return IconRegistry.conflict_supernatural_icon()
        elif type == ConflictType.SELF:
            return IconRegistry.conflict_self_icon()

    @staticmethod
    def conflict_character_icon() -> QIcon:
        return IconRegistry.character_icon(color='#c1666b', color_on=CONFLICT_CHARACTER_COLOR)

    @staticmethod
    def conflict_society_icon() -> QIcon:
        return IconRegistry.from_name('ei.group-alt', color=CONFLICT_SOCIETY_COLOR)

    @staticmethod
    def conflict_nature_icon() -> QIcon:
        return IconRegistry.from_name('mdi.weather-hurricane', color=CONFLICT_NATURE_COLOR)

    @staticmethod
    def conflict_technology_icon() -> QIcon:
        return IconRegistry.from_name('ei.cogs', color=CONFLICT_TECHNOLOGY_COLOR)

    @staticmethod
    def conflict_supernatural_icon() -> QIcon:
        return IconRegistry.from_name('mdi.creation', color=CONFLICT_SUPERNATURAL_COLOR)

    @staticmethod
    def conflict_self_icon(color: str = CONFLICT_SELF_COLOR, color_on: str = CONFLICT_SELF_COLOR) -> QIcon:
        return IconRegistry.from_name('mdi.mirror', color=color, color_on=color_on)

    @staticmethod
    def subplot_icon(color: str = 'black') -> QIcon:
        return IconRegistry.from_name('mdi.source-branch', color=color)

    @staticmethod
    def baby_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.baby')

    @staticmethod
    def child_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.child')

    @staticmethod
    def teenager_icon() -> QIcon:
        return IconRegistry.from_name('mdi.human')

    @staticmethod
    def adult_icon() -> QIcon:
        return IconRegistry.from_name('ei.adult')

    @staticmethod
    def elderly_icon() -> QIcon:
        return IconRegistry.from_name('mdi.human-cane')

    @staticmethod
    def cog_icon(**kwargs) -> QIcon:
        return IconRegistry.from_name('fa5s.cog', **kwargs)

    @staticmethod
    def cause_icon(color: str = 'black') -> QIcon:
        return IconRegistry.from_name('mdi.ray-start', color=color)

    @staticmethod
    def cause_and_effect_icon(color: str = 'black', color_on: str = 'black') -> QIcon:
        return IconRegistry.from_name('mdi.ray-start-arrow', color=color, color_on=color_on)

    @staticmethod
    def reversed_cause_and_effect_icon() -> QIcon:
        return IconRegistry.from_name('mdi.ray-end-arrow')

    @staticmethod
    def toggle_on_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.toggle-on')

    @staticmethod
    def toggle_off_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.toggle-off')

    @staticmethod
    def heading_1_icon() -> QIcon:
        return IconRegistry.from_name('mdi.format-header-1', scale=1.4)

    @staticmethod
    def heading_2_icon() -> QIcon:
        return IconRegistry.from_name('mdi.format-header-2')

    @staticmethod
    def dots_icon(color: str = 'black', vertical: bool = False) -> QIcon:
        return IconRegistry.from_name('mdi.dots-vertical' if vertical else 'mdi.dots-horizontal', color)

    @staticmethod
    def icons_icon(color: str = 'black') -> QIcon:
        return IconRegistry.from_name('fa5s.icons', color)

    @staticmethod
    def template_icon() -> QIcon:
        return IconRegistry.from_name('ei.magic', color='#35a7ff')

    @staticmethod
    def circle_icon(**kwargs) -> QIcon:
        return IconRegistry.from_name('mdi.circle-medium', **kwargs)

    @staticmethod
    def inciting_incident_icon(color: str = '#a2ad59') -> QIcon:
        return IconRegistry.from_name('mdi.bell-alert-outline', color)

    @staticmethod
    def hook_icon() -> QIcon:
        return IconRegistry.from_name('mdi.hook', '#829399')

    @staticmethod
    def rising_action_icon(color: str = '#08605f', color_on: str = '#08605f') -> QIcon:
        return IconRegistry.from_name('fa5s.chart-line', color=color, color_on=color_on)

    @staticmethod
    def setback_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.chart-line', color='#FD4D21', vflip=True)

    @staticmethod
    def crisis_icon(color: str = '#ce2d4f', color_on: str = '#ce2d4f') -> QIcon:
        return IconRegistry.from_name('mdi.arrow-decision-outline', color=color, color_on=color_on)

    @staticmethod
    def tool_icon(color: str = '#d4a373', color_on: str = '#d4a373') -> QIcon:
        return IconRegistry.from_name('fa5s.hammer', color, color_on)

    @staticmethod
    def cost_icon(color: str = '#e9c46a', color_on: str = '#e9c46a') -> QIcon:
        return IconRegistry.from_name('ph.coin-bold', color, color_on)

    @staticmethod
    def ticking_clock_icon() -> QIcon:
        return IconRegistry.from_name('mdi.clock-alert-outline', '#f7cb15')

    @staticmethod
    def exposition_icon() -> QIcon:
        return IconRegistry.from_name('fa5.image', '#1ea896')

    @staticmethod
    def beat_icon() -> QIcon:
        return IconRegistry.from_name('mdi.lightning-bolt-outline')

    @staticmethod
    def timer_icon() -> QIcon:
        return IconRegistry.from_name('mdi.timer-outline')

    @staticmethod
    def theme_icon(color: str = '#9d4edd', color_on: str = '#9d4edd') -> QIcon:
        return IconRegistry.from_name('mdi.butterfly-outline', color=color, color_on=color_on)

    @staticmethod
    def pause_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.pause', '#3f37c9')

    @staticmethod
    def play_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.play', '#2a9d8f')

    @staticmethod
    def context_icon() -> QIcon:
        return IconRegistry.from_name('mdi.menu')

    @staticmethod
    def story_structure_icon(**kwargs) -> QIcon:
        return IconRegistry.from_name('mdi6.bridge', **kwargs, scale=1.4)

    @staticmethod
    def plot_icon(**kwargs) -> QIcon:
        return IconRegistry.from_name('mdi.chart-bell-curve-cumulative', **kwargs)

    @staticmethod
    def storylines_icon(**kwargs) -> QIcon:
        return IconRegistry.from_name('fa5s.theater-masks', **kwargs)

    @staticmethod
    def plot_type_icon(plot_type: PlotType) -> QIcon:
        if plot_type == PlotType.Main:
            return IconRegistry.cause_and_effect_icon()
        elif plot_type == PlotType.Internal:
            return IconRegistry.conflict_self_icon()
        elif plot_type == PlotType.Subplot:
            return IconRegistry.from_name('mdi.source-branch')

    @staticmethod
    def charge_icon(charge: int = 1) -> QIcon:
        if charge == 0:
            return IconRegistry.from_name('mdi.wave', 'grey')
        elif charge == 1:
            return IconRegistry.from_name('mdi.chevron-up', '#2d6a4f')
        elif charge == 2:
            return IconRegistry.from_name('mdi.chevron-double-up', '#40916c')
        elif charge >= 3:
            return IconRegistry.from_name('mdi.chevron-triple-up', '#52b788')
        elif charge == -1:
            return IconRegistry.from_name('mdi.chevron-down', '#dc2f02')
        elif charge == -2:
            return IconRegistry.from_name('mdi.chevron-double-down', '#d00000')
        else:
            return IconRegistry.from_name('mdi.chevron-triple-down', '#9d0208')

    @staticmethod
    def male_gender_icon(color: str = 'black') -> QIcon:
        return IconRegistry.from_name('mdi.gender-male', color=color, color_on='#067bc2')

    @staticmethod
    def female_gender_icon(color: str = 'black') -> QIcon:
        return IconRegistry.from_name('mdi.gender-female', color=color, color_on='#832161')

    @staticmethod
    def transgender_icon(color: str = 'black') -> QIcon:
        return IconRegistry.from_name('fa5s.transgender-alt', color=color, color_on='#f4a261')

    @staticmethod
    def non_binary_gender_icon(color: str = 'black') -> QIcon:
        return IconRegistry.from_name('mdi.gender-male-female-variant', color=color, color_on='#7209b7')

    @staticmethod
    def genderless_icon(color: str = 'black') -> QIcon:
        return IconRegistry.from_name('fa5s.genderless', color=color, color_on='#6c757d')

    @staticmethod
    def gender_icon(gender: str):
        if gender == MALE:
            return IconRegistry.male_gender_icon('#067bc2')
        if gender == FEMALE:
            return IconRegistry.female_gender_icon('#832161')
        if gender == TRANSGENDER:
            return IconRegistry.transgender_icon('#f4a261')
        if gender == NON_BINARY:
            return IconRegistry.non_binary_gender_icon('#7209b7')
        if gender == GENDERLESS:
            return IconRegistry.genderless_icon('#6c757d')

    @staticmethod
    def backstory_icon(color: str = '#9c6644', color_on='#9c6644') -> QIcon:
        return IconRegistry.from_name('fa5s.archive', color, color_on)

    @staticmethod
    def topics_icon(color: str = 'black', color_on='darkBlue') -> QIcon:
        return IconRegistry.from_name('mdi.card-account-details-star-outline', color, color_on)

    @staticmethod
    def big_five_icon(color_on: str = '#7209b7') -> QIcon:
        return IconRegistry.from_name('ph.number-square-five-bold', color_on=color_on)

    @staticmethod
    def expand_icon() -> QIcon:
        return IconRegistry.from_name('fa5s.expand-alt', vflip=True)

    @staticmethod
    def group_icon() -> QIcon:
        return IconRegistry.from_name('mdi.account-group')

    @staticmethod
    def docx_icon() -> QIcon:
        return IconRegistry.from_name('mdi.file-word-outline')

    @staticmethod
    def refresh_icon(color: str = PLOTLYST_MAIN_COLOR) -> QIcon:
        return IconRegistry.from_name('ei.refresh', color=color)

    @staticmethod
    def from_selection_item(item: SelectionItem) -> QIcon:
        return IconRegistry.from_name(item.icon, item.icon_color)

    @staticmethod
    def from_name(name: str, color: str = 'black', color_on: str = '', scale: Optional[float] = None,
                  hflip: bool = False,
                  vflip: bool = False, rotated: int = 0) -> QIcon:
        _color_on = color_on if color_on else color

        icon_args = {
            'color': color,
            'color_on': _color_on
        }

        if (scale is not None) or (
                name.startswith('md') or name.startswith('ri') or name.startswith('ph') or name.startswith('msc')):
            if scale is not None:
                icon_args['options'] = [{'scale_factor': scale}]
            elif scale is None and (
                    name.startswith('md') or name.startswith('ri') or name.startswith('ph') or name.startswith('msc')):
                icon_args['options'] = [{'scale_factor': 1.2}]

        if hflip is not None:
            icon_args['hflip'] = hflip
        if vflip is not None:
            icon_args['vflip'] = vflip
        if rotated != 0:
            icon_args['rotated'] = rotated

        return QIcon(qtawesome.icon(name, **icon_args))


class AvatarsRegistry:
    def __init__(self):
        self._images: Dict[Character, QPixmap] = {}

    def avatar(self, character: Character, fallback: bool = True) -> QIcon:
        if character.prefs.avatar.use_image and character.avatar:
            return QIcon(self.image(character))
        elif character.prefs.avatar.use_role and character.role:
            return IconRegistry.from_name(character.role.icon, character.role.icon_color)
        elif character.prefs.avatar.use_custom_icon and character.prefs.avatar.icon:
            return IconRegistry.from_name(character.prefs.avatar.icon, character.prefs.avatar.icon_color)
        elif character.prefs.avatar.use_initial and self.has_name_initial_icon(character):
            return self.name_initial_icon(character, fallback)

        if fallback:
            return self._dummy_avatar()
        else:
            return None

    def image(self, character: Character) -> QPixmap:
        if character in self._images.keys():
            return self._images[character]

        pixmap = QPixmap()
        if not character.avatar:
            return pixmap

        pixmap.loadFromData(character.avatar)
        rounded = rounded_pixmap(pixmap)
        self._images[character] = rounded

        return rounded

    def has_name_initial_icon(self, character: Character) -> bool:
        if character.name and (character.name[0].isnumeric() or character.name[0].isalpha()):
            return True
        return False

    def name_initial_icon(self, character: Character, fallback: bool = True) -> QIcon:
        _sum = sum([ord(x) for x in character.name])
        color = CHARACTER_INITIAL_AVATAR_COLOR_CODES[_sum % len(CHARACTER_INITIAL_AVATAR_COLOR_CODES)]

        if not character.name:
            return self._dummy_avatar()

        if character.name[0].isnumeric():
            icon = f'mdi.numeric-{int(character.name[0])}-circle-outline'
        elif character.name[0].isalpha():
            icon = f'mdi.alpha-{character.name[0].lower()}-circle-outline'
        elif fallback:
            return self._dummy_avatar()
        else:
            return None

        return IconRegistry.from_name(icon, color)

    def update_image(self, character: Character):
        if character in self._images.keys():
            self._images.pop(character)
        self.image(character)

    def _dummy_avatar(self) -> QIcon:
        return IconRegistry.character_icon(color_on='black')


avatars = AvatarsRegistry()


def set_avatar(label: QLabel, character: Character, size: int = 128):
    avatar = avatars.avatar(character, fallback=False)
    if avatar:
        label.setPixmap(avatar.pixmap(size, size))
    else:
        label.setPixmap(IconRegistry.portrait_icon().pixmap(QSize(size, size)))
