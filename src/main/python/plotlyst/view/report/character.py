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
from typing import Optional, List

from PyQt6.QtCharts import QPolarChart, QCategoryAxis, QLineSeries, QAreaSeries
from PyQt6.QtCharts import QValueAxis, QSplineSeries
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPen
from PyQt6.QtWidgets import QLabel, QWidget, QToolButton
from overrides import overrides
from qthandy import clear_layout, vspacer, hbox, transparent, vbox

from src.main.python.plotlyst.core.domain import Novel, Character, Scene, SceneType
from src.main.python.plotlyst.core.text import html
from src.main.python.plotlyst.view.common import icon_to_html_img
from src.main.python.plotlyst.view.generated.report.character_arc_report_ui import Ui_CharacterArcReport
from src.main.python.plotlyst.view.generated.report.character_report_ui import Ui_CharacterReport
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.report import AbstractReport
from src.main.python.plotlyst.view.widget.characters import CharacterEmotionButton
from src.main.python.plotlyst.view.widget.chart import BaseChart, SupporterRoleChart, GenderCharacterChart, \
    PolarBaseChart


class CharacterReport(AbstractReport, Ui_CharacterReport):

    def __init__(self, novel: Novel, parent=None):
        super(CharacterReport, self).__init__(novel, parent)

        self._chartRoles = SupporterRoleChart()
        self.chartViewRoles.setChart(self._chartRoles)

        self._chartGenderAll = GenderCharacterChart()
        self.chartViewGenderAll.setChart(self._chartGenderAll)

        self._chartGenderMajor = GenderCharacterChart()
        self._chartGenderMajor.setTitle(html('Gender per major roles').bold())
        self._chartGenderMajor.setLabelsVisible(False)
        self.chartViewGenderMajor.setChart(self._chartGenderMajor)

        self._chartGenderSecondary = GenderCharacterChart()
        self._chartGenderSecondary.setTitle(html('Gender per secondary roles').bold())
        self._chartGenderSecondary.setLabelsVisible(False)
        self.chartViewGenderSecondary.setChart(self._chartGenderSecondary)

        self._chartGenderMinor = GenderCharacterChart()
        self._chartGenderMinor.setTitle(html('Gender per minor roles').bold())
        self._chartGenderMinor.setLabelsVisible(False)
        self.chartViewGenderMinor.setChart(self._chartGenderMinor)

        self._chartAge = AgeChart()
        self.chartViewAge.setChart(self._chartAge)

        self.refresh()

    @overrides
    def refresh(self):
        self._chartRoles.refresh(self.novel.characters)
        self._chartGenderAll.refresh(self.novel.characters)
        self._chartGenderMajor.refresh(self.novel.major_characters())
        self._chartGenderSecondary.refresh(self.novel.secondary_characters())
        self._chartGenderMinor.refresh(self.novel.minor_characters())
        self._chartAge.refresh(self.novel.characters)


class AgeChart(PolarBaseChart):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(html('Age distribution').bold())

        self._rad_axis = QValueAxis()
        self._rad_axis.setLabelsVisible(False)
        self._angular_axis = QCategoryAxis()
        self._angular_axis.setRange(0, 45)
        self._angular_axis.append(icon_to_html_img(IconRegistry.baby_icon()), 3)
        self._angular_axis.append(icon_to_html_img(IconRegistry.child_icon()), 10)
        self._angular_axis.append(icon_to_html_img(IconRegistry.teenager_icon()), 15)
        self._angular_axis.append(icon_to_html_img(IconRegistry.adult_icon()), 35)

    def refresh(self, characters: List[Character]):
        self.reset()

        self.addAxis(self._rad_axis, QPolarChart.PolarOrientation.PolarOrientationRadial)
        self.addAxis(self._angular_axis, QPolarChart.PolarOrientation.PolarOrientationAngular)

        pen = QPen()
        pen.setWidth(2)
        pen.setColor(Qt.GlobalColor.darkBlue)

        upper_series = QLineSeries()
        upper_series.setPen(pen)
        lower_series = QLineSeries()
        lower_series.setPen(pen)

        ages = {}
        for char in characters:
            if not char.age:
                continue
            age = 45 if char.age > 45 else char.age
            if age not in ages.keys():
                ages[age] = 1
            ages[age] = ages[age] + 1
        sorted_ages = sorted(ages.keys())
        if sorted_ages:
            upper_series.append(sorted_ages[0], 0)
            for age in sorted_ages:
                upper_series.append(age, ages[age])
                lower_series.append(age, 0)
            upper_series.append(sorted_ages[-1], 0)

        if ages:
            self._rad_axis.setRange(0, max(ages.values()))

        self.addSeries(upper_series)
        self.addSeries(lower_series)

        series = QAreaSeries(upper_series, lower_series)
        series.setColor(Qt.GlobalColor.darkBlue)
        series.setPen(pen)

        self.addSeries(series)
        series.attachAxis(self._rad_axis)
        series.attachAxis(self._angular_axis)


class SceneArcWidget(QWidget):
    arcChanged = pyqtSignal(Scene)

    def __init__(self, scene: Scene, novel: Novel, parent=None):
        super(SceneArcWidget, self).__init__(parent)
        hbox(self, 0, 2)

        self.scene = scene

        self.btnSceneType = QToolButton()
        transparent(self.btnSceneType)
        if scene.type != SceneType.DEFAULT:
            self.btnSceneType.setIcon(IconRegistry.scene_type_icon(scene))
        self.lblTitle = QLabel(scene.title_or_index(novel))
        self.btnEndingEmotion = CharacterEmotionButton()
        self.btnEndingEmotion.setValue(scene.agendas[0].ending_emotion)
        self.btnEndingEmotion.emotionChanged.connect(self._emotionChanged)

        self.layout().addWidget(self.btnSceneType)
        self.layout().addWidget(self.lblTitle)
        self.layout().addWidget(self.btnEndingEmotion)

    def _emotionChanged(self):
        self.scene.agendas[0].ending_emotion = self.btnEndingEmotion.value()
        self.arcChanged.emit(self.scene)


class CharacterArcReport(AbstractReport, Ui_CharacterArcReport):

    def __init__(self, novel: Novel, parent=None):
        super(CharacterArcReport, self).__init__(novel, parent)
        self.wdgCharacterSelector.characterToggled.connect(self._characterChanged)
        self.chart = CharacterArcChart(self.novel)
        self.chartView.setChart(self.chart)
        vbox(self.wdgScenes)
        self.btnScenes.setIcon(IconRegistry.scene_icon())

        self.character: Optional[Character] = None

        self.refresh()

    @overrides
    def refresh(self):
        self.wdgCharacterSelector.setCharacters(self.novel.agenda_characters(), checkAll=False)

    def _characterChanged(self, character: Character, toggled: bool):
        if not toggled:
            return
        self.character = character
        self.chart.refresh(character)
        clear_layout(self.wdgScenes)
        for scene in self.novel.scenes:
            if scene.agendas[0].character_id != character.id:
                continue
            wdgArc = SceneArcWidget(scene, self.novel)
            wdgArc.arcChanged.connect(self._arcChanged)
            self.wdgScenes.layout().addWidget(wdgArc)
        self.wdgScenes.layout().addWidget(vspacer())

    def _arcChanged(self, scene: Scene):
        self.repo.update_scene(scene)
        self.chart.refresh(self.character)


class CharacterArcChart(BaseChart):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.createDefaultAxes()
        self.axis: Optional[QValueAxis] = None

    def refresh(self, character: Character):
        self.removeAllSeries()
        if self.axis:
            self.removeAxis(self.axis)
        self.setTitle(f'<b>Emotional arc of {character.name}</b>')

        series = QSplineSeries()
        arc_value: int = 0
        series.append(0, 0)
        for scene in self.novel.scenes:
            if scene.agendas[0].character_id != character.id:
                continue
            arc_value += scene.agendas[0].ending_emotion
            series.append(len(series), arc_value)

        # if not series.count():
        #     return

        # min_ = min([x.y() for x in points])
        # max_ = max([x.y() for x in points])
        # limit = max(abs(min_), max_)
        # self.axis = QValueAxis()
        # self.axis.setRange(-limit - 3, limit + 3)
        self.addSeries(series)
        # self.addAxis(self.axis, Qt.AlignmentFlag.AlignLeft)
        # self.axis.setVisible(False)
