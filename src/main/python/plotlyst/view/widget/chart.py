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
from typing import List, Dict

from PyQt5.QtChart import QChart, QPieSeries
from PyQt5.QtGui import QColor

from src.main.python.plotlyst.core.domain import Character, MALE, FEMALE, TRANSGENDER, NON_BINARY, GENDERLESS
from src.main.python.plotlyst.core.template import enneagram_choices, supporter_role, guide_role, sidekick_role, \
    antagonist_role, contagonist_role, adversary_role, henchmen_role, confidant_role, tertiary_role, SelectionItem, \
    secondary_role
from src.main.python.plotlyst.view.common import icon_to_html_img
from src.main.python.plotlyst.view.icons import IconRegistry


class BaseChart(QChart):
    def __init__(self, parent=None):
        super(BaseChart, self).__init__(parent)
        self.setAnimationOptions(QChart.SeriesAnimations)
        self.setAnimationDuration(500)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.legend().hide()
        self.setBackgroundRoundness(0)


class GenderCharacterChart(BaseChart):

    def refresh(self, characters: List[Character]):
        series = QPieSeries()

        genders: Dict[str, int] = {}
        for char in characters:
            if not char.gender:
                continue
            if char.gender not in genders.keys():
                genders[char.gender] = 0
            genders[char.gender] = genders[char.gender] + 1

        for k, v in genders.items():
            if v:
                slice_ = series.append(k, v)
                slice_.setLabelVisible()
                slice_.setLabel(k.capitalize())
                slice_.setColor(QColor(self._colorForGender(k)))

        if self.series():
            self.removeAllSeries()
        self.addSeries(series)

    def _colorForGender(self, gender: str) -> str:
        if gender == MALE:
            return '#067bc2'
        elif gender == FEMALE:
            return '#832161'
        elif gender == TRANSGENDER:
            return '#f4a261'
        elif gender == NON_BINARY:
            return '#7209b7'
        elif gender == GENDERLESS:
            return '#6c757d'


class SupporterRoleChart(BaseChart):

    def refresh(self, characters: List[Character]):
        series = QPieSeries()

        supporter = 0
        adversary = 0
        secondary = 0
        tertiary = 0
        for char in characters:
            if not char.role:
                continue
            if char.role in [supporter_role, guide_role, sidekick_role, confidant_role]:
                supporter += 1
            elif char.role in [antagonist_role, contagonist_role, adversary_role, henchmen_role]:
                adversary += 1
            elif char.role is tertiary_role:
                tertiary += 1
            else:
                secondary += 1
        if supporter:
            self._addSlice(series, supporter_role, supporter)
        if adversary:
            self._addSlice(series, adversary_role, adversary)
        if tertiary:
            self._addSlice(series, tertiary_role, tertiary)
        if secondary:
            self._addSlice(series, secondary_role, secondary)

        for slice_ in series.slices():
            slice_.setLabelVisible()

        if self.series():
            self.removeAllSeries()
        self.addSeries(series)

    def _addSlice(self, series: QPieSeries, role: SelectionItem, value: int):
        slice_ = series.append(
            icon_to_html_img(IconRegistry.from_name(role.icon, role.icon_color)), value)
        slice_.setColor(QColor(role.icon_color))


class EnneagramChart(BaseChart):

    def refresh(self, characters: List[Character]):
        series = QPieSeries()

        enneagrams: Dict[str, int] = {}
        for char in characters:
            enneagram = char.enneagram()
            if not enneagram:
                continue
            if enneagram.text not in enneagrams.keys():
                enneagrams[enneagram.text] = 0
            enneagrams[enneagram.text] = enneagrams[enneagram.text] + 1

        for k, v in enneagrams.items():
            slice_ = series.append(k, v)
            slice_.setLabelVisible()
            item = enneagram_choices[k]
            slice_.setLabel(icon_to_html_img(IconRegistry.from_name(item.icon, item.icon_color)))
            slice_.setColor(QColor(item.icon_color))

        if self.series():
            self.removeAllSeries()
        self.addSeries(series)
