"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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

EXIT_CODE_RESTART = 10

WIP_COLOR: str = '#f6cd61'
PIVOTAL_COLOR: str = '#3da4ab'

ACT_ONE_COLOR: str = '#02bcd4'
ACT_TWO_COLOR: str = '#1bbc9c'
ACT_THREE_COLOR: str = '#ff7800'

CONFLICT_CHARACTER_COLOR: str = '#c1666b'
CONFLICT_SOCIETY_COLOR: str = '#69306d'
CONFLICT_NATURE_COLOR: str = '#157a6e'
CONFLICT_TECHNOLOGY_COLOR: str = '#4a5859'
CONFLICT_SUPERNATURAL_COLOR: str = '#ac7b84'
CONFLICT_SELF_COLOR: str = '#94b0da'

RELAXED_WHITE_COLOR: str = '#f8f9fa'


def truncate_string(text: str, length: int = 25):
    return (text[:length] + '...') if len(text) > length else text
