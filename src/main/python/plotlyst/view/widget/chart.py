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
from typing import List, Dict

from PyQt6.QtCharts import QChart, QPieSeries, QBarSet, QBarCategoryAxis, QValueAxis, QBarSeries, QSplineSeries, \
    QPolarChart
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor, QIcon
from PyQt6.QtWidgets import QToolTip
from overrides import overrides

from src.main.python.plotlyst.common import ACT_ONE_COLOR, ACT_TWO_COLOR, ACT_THREE_COLOR
from src.main.python.plotlyst.core.domain import Character, MALE, FEMALE, TRANSGENDER, NON_BINARY, GENDERLESS, Novel, \
    SceneStructureItem
from src.main.python.plotlyst.core.template import enneagram_choices, supporter_role, guide_role, sidekick_role, \
    antagonist_role, contagonist_role, adversary_role, henchmen_role, confidant_role, tertiary_role, SelectionItem, \
    secondary_role
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.view.common import icon_to_html_img
from src.main.python.plotlyst.view.icons import IconRegistry


class _AbstractChart:

    def __init__(self, _=None):
        self.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.setAnimationDuration(500)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.legend().hide()
        self.setBackgroundRoundness(0)

    def reset(self):
        if self.series():
            self.removeAllSeries()


class BaseChart(QChart, _AbstractChart):
    def __init__(self, parent=None):
        super().__init__(parent)

    @overrides
    def reset(self):
        super(BaseChart, self).reset()
        h_axis = self.axes(Qt.Orientation.Horizontal)
        if h_axis:
            self.removeAxis(h_axis[0])
        y_axis = self.axes(Qt.Orientation.Vertical)
        if y_axis:
            self.removeAxis(y_axis[0])


class PolarBaseChart(QPolarChart, _AbstractChart):
    def __init__(self, parent=None):
        super().__init__(parent)

    @overrides
    def reset(self):
        super(PolarBaseChart, self).reset()
        p_axis = self.axes(QPolarChart.PolarOrientation.PolarOrientationAngular)
        if p_axis:
            for ax in p_axis:
                self.removeAxis(ax)
        a_axis = self.axes(QPolarChart.PolarOrientation.PolarOrientationAngular)
        if a_axis:
            for ax in a_axis:
                self.removeAxis(ax)


class GenderCharacterChart(BaseChart):

    def __init__(self, parent=None):
        super(GenderCharacterChart, self).__init__(parent)
        self.setTitle('<b>Gender</b>')
        self._labelsVisible: bool = True

    def setLabelsVisible(self, visible: bool):
        self._labelsVisible = visible

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
                slice_.setLabelVisible(self._labelsVisible)
                slice_.setLabel(icon_to_html_img(self._iconForGender(k)))
                slice_.setLabelArmLengthFactor(0.2)
                slice_.hovered.connect(partial(self._hovered, k))
                slice_.setColor(QColor(self._colorForGender(k)))

        if self.series():
            self.removeAllSeries()
        self.addSeries(series)

    def _hovered(self, gender: str, state: bool):
        if state:
            QToolTip.showText(QCursor.pos(),
                              f'<b style="color: {self._colorForGender(gender)}">{gender.capitalize()}</b>')
        else:
            QToolTip.hideText()

    def _iconForGender(self, gender: str) -> QIcon:
        if gender == MALE:
            return IconRegistry.male_gender_icon(self._colorForGender(gender))
        elif gender == FEMALE:
            return IconRegistry.female_gender_icon(self._colorForGender(gender))
        elif gender == TRANSGENDER:
            return IconRegistry.transgender_icon(self._colorForGender(gender))
        elif gender == NON_BINARY:
            return IconRegistry.non_binary_gender_icon(self._colorForGender(gender))
        elif gender == GENDERLESS:
            return IconRegistry.genderless_icon(self._colorForGender(gender))
        else:
            IconRegistry.empty_icon()

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
        else:
            return 'black'


class SupporterRoleChart(BaseChart):

    def __init__(self, parent=None):
        super(SupporterRoleChart, self).__init__(parent)
        self.setTitle('<b>Supporter/adversary role</b>')

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
            slice_.setLabelArmLengthFactor(0.2)

        if self.series():
            self.removeAllSeries()
        self.addSeries(series)

    def _addSlice(self, series: QPieSeries, role: SelectionItem, value: int):
        slice_ = series.append(
            icon_to_html_img(IconRegistry.from_name(role.icon, role.icon_color)), value)
        slice_.setColor(QColor(role.icon_color))
        slice_.hovered.connect(partial(self._hovered, role))

    def _hovered(self, role: SelectionItem, state: bool):
        if state:
            QToolTip.showText(QCursor.pos(), f'<b style="color: {role.icon_color}">{role.text.capitalize()}</b>')
        else:
            QToolTip.hideText()


class EnneagramChart(BaseChart):

    def __init__(self, parent=None):
        super(EnneagramChart, self).__init__(parent)
        self.setTitle('<b>Enneagram</b>')

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
            slice_.setLabelArmLengthFactor(0.2)
            slice_.setColor(QColor(item.icon_color))
            slice_.hovered.connect(partial(self._hovered, item))

        if self.series():
            self.removeAllSeries()
        self.addSeries(series)

    def _hovered(self, enneagram: SelectionItem, state: bool):
        if state:
            QToolTip.showText(QCursor.pos(),
                              f'<b style="color: {enneagram.icon_color}">{enneagram.text.capitalize()}</b>')
        else:
            QToolTip.hideText()


class ManuscriptLengthChart(BaseChart):
    def __init__(self, parent=None):
        super(ManuscriptLengthChart, self).__init__(parent)
        self.setTitle('<b>Manuscript length per chapters</b>')

    def refresh(self, novel: Novel):
        self.reset()

        self.setMinimumWidth(max(len(novel.chapters), 15) * 35)

        set_ = QBarSet('Chapter')
        for i, chapter in enumerate(novel.chapters):
            chapter_wc = 0
            for scene in novel.scenes_in_chapter(chapter):
                if scene.manuscript and scene.manuscript.statistics:
                    chapter_wc += scene.manuscript.statistics.wc
            set_.append(chapter_wc)

        series = QBarSeries()
        series.append(set_)

        axis_x = QBarCategoryAxis()
        axis_x_values = [*range(1, len(novel.chapters) + 1)]
        axis_x_values = [str(x) for x in axis_x_values]
        axis_x.append(axis_x_values)
        self.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)

        axis_y = QValueAxis()
        self.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

        self.addSeries(series)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)


class SceneStructureEmotionalArcChart(BaseChart):

    def refresh(self, beats: List[SceneStructureItem]):
        self.reset()

        series = QSplineSeries()
        arc_value: int = 0
        series.append(0, 0)
        for beat in beats:
            if beat.emotion is not None:
                arc_value = beat.emotion * 2
            series.append(len(series), arc_value)

        axis = QValueAxis()
        axis.setRange(-8, 8)
        self.addSeries(series)
        self.setAxisY(axis, series)
        axis.setVisible(False)


class ActDistributionChart(BaseChart):

    def __init__(self, parent=None):
        super(ActDistributionChart, self).__init__(parent)
        self.setTitle('<b>Act distribution</b>')
        self.legend().setVisible(True)
        self.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

    def refresh(self, novel: Novel):
        self.reset()

        series = QPieSeries()

        acts: Dict[int, int] = {}
        for scene in novel.scenes:
            act = acts_registry.act(scene)
            if act not in acts.keys():
                acts[act] = 0
            acts[act] = acts[act] + 1

        for k, v in acts.items():
            slice_ = series.append(f'Act {k}', v)

            if k == 1:
                color = ACT_ONE_COLOR
            elif k == 2:
                color = ACT_TWO_COLOR
            else:
                color = ACT_THREE_COLOR
            slice_.setColor(QColor(color))

        self.addSeries(series)
