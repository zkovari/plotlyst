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
from src.main.python.plotlyst.core.domain import VERY_UNHAPPY, UNHAPPY, HAPPY, VERY_HAPPY

EXIT_CODE_RESTART = 10

WIP_COLOR: str = '#f6cd61'
PIVOTAL_COLOR: str = '#3da4ab'

ACT_ONE_COLOR: str = '#02bcd4'
TRANS_ACT_ONE_COLOR: str = 'rgba(2, 188, 212, 45)'
ACT_TWO_COLOR: str = '#1bbc9c'
TRANS_ACT_TWO_COLOR: str = 'rgba(27, 188, 156, 45)'
ACT_THREE_COLOR: str = '#ff7800'
TRANS_ACT_THREE_COLOR: str = 'rgba(255, 120, 0, 45)'

CONFLICT_CHARACTER_COLOR: str = '#c1666b'
CONFLICT_SOCIETY_COLOR: str = '#69306d'
CONFLICT_NATURE_COLOR: str = '#157a6e'
CONFLICT_TECHNOLOGY_COLOR: str = '#4a5859'
CONFLICT_SUPERNATURAL_COLOR: str = '#ac7b84'
CONFLICT_SELF_COLOR: str = '#94b0da'

CHARACTER_MAJOR_COLOR: str = '#00798c'
CHARACTER_SECONDARY_COLOR: str = '#619b8a'
CHARACTER_MINOR_COLOR: str = '#886f68'

NEUTRAL_EMOTION_COLOR: str = '#ababab'
VERY_UNHAPPY_EMOTION_COLOR: str = '#ef0000'
UNHAPPY_EMOTION_COLOR: str = '#ff8e2b'
HAPPY_EMOTION_COLOR: str = '#93e5ab'
VERY_HAPPY_EMOTION_COLOR: str = '#00ca94'

PLOTLYST_MAIN_COLOR: str = '#3C0764'  # Persian indigo, #4B0763: Indigo, #37065D: Russian violet
PLOTLYST_MAIN_COMPLEMENTARY_COLOR: str = '#2C5D06'  # Dark moss green
PLOTLYST_SECONDARY_COLOR: str = '#4B0763'  # Persian indigo
PLOTLYST_TERTIARY_COLOR: str = '#D4B8E0'  # Thistle

RELAXED_WHITE_COLOR: str = '#f8f9fa'


def emotion_color(emotion_value: int) -> str:
    if emotion_value == VERY_UNHAPPY:
        return VERY_UNHAPPY_EMOTION_COLOR
    elif emotion_value == UNHAPPY:
        return UNHAPPY_EMOTION_COLOR
    elif emotion_value == HAPPY:
        return HAPPY_EMOTION_COLOR
    elif emotion_value == VERY_HAPPY:
        return VERY_HAPPY_EMOTION_COLOR
    else:
        return NEUTRAL_EMOTION_COLOR


EM_DASH = u'\u2014'
EN_DASH = u'\u2013'
LEFT_QUOTATION_ENGLISH = u'\u201C'
RIGHT_QUOTATION_ENGLISH = u'\u201D'


def truncate_string(text: str, length: int = 25):
    return (text[:length] + '...') if len(text) > length else text


def act_color(act: int, translucent: bool = False) -> str:
    if act == 1:
        return TRANS_ACT_ONE_COLOR if translucent else ACT_ONE_COLOR
    elif act == 2:
        return TRANS_ACT_TWO_COLOR if translucent else ACT_TWO_COLOR
    elif act == 3:
        return TRANS_ACT_THREE_COLOR if translucent else ACT_THREE_COLOR
    else:
        return '#DBF5FA'


def recursive(parent, children_func, action):
    for child in children_func(parent):
        action(parent, child)
        recursive(child, children_func, action)
