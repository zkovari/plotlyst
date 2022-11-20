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
from functools import partial
from typing import Optional

from PyQt6.QtCharts import QPieSeries
from PyQt6.QtCharts import QValueAxis, QSplineSeries
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QWidget, QToolButton
from overrides import overrides
from qthandy import clear_layout, vspacer, hbox, transparent, vbox

from src.main.python.plotlyst.core.domain import Novel, Character, Scene, SceneType
from src.main.python.plotlyst.core.text import html
from src.main.python.plotlyst.service.cache import acts_registry
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

        self.btnAct1.setIcon(IconRegistry.act_one_icon())
        self.btnAct2.setIcon(IconRegistry.act_two_icon())
        self.btnAct3.setIcon(IconRegistry.act_three_icon())

        self._povChart = PovDistributionChart()
        self.chartView.setChart(self._povChart)
        self.btnAct1.toggled.connect(partial(self._povChart.toggleAct, 1))
        self.btnAct2.toggled.connect(partial(self._povChart.toggleAct, 2))
        self.btnAct3.toggled.connect(partial(self._povChart.toggleAct, 3))
        self._povChart.refresh(novel)

        self._chartRoles = SupporterRoleChart()
        self._chartRoles.refresh(novel.characters)
        self.chartViewRoles.setChart(self._chartRoles)

        self._chartGenderAll = GenderCharacterChart()
        self._chartGenderAll.refresh(novel.characters)
        self.chartViewGenderAll.setChart(self._chartGenderAll)

        self._chartGenderMajor = GenderCharacterChart()
        self._chartGenderMajor.setTitle(html('Gender per major roles').bold())
        self._chartGenderMajor.setLabelsVisible(False)
        self._chartGenderMajor.refresh(novel.major_characters())
        self.chartViewGenderMajor.setChart(self._chartGenderMajor)

        self._chartGenderSecondary = GenderCharacterChart()
        self._chartGenderSecondary.setTitle(html('Gender per secondary roles').bold())
        self._chartGenderSecondary.setLabelsVisible(False)
        self._chartGenderSecondary.refresh(novel.secondary_characters())
        self.chartViewGenderSecondary.setChart(self._chartGenderSecondary)

        self._chartGenderMinor = GenderCharacterChart()
        self._chartGenderMinor.setTitle(html('Gender per minor roles').bold())
        self._chartGenderMinor.setLabelsVisible(False)
        self._chartGenderMinor.refresh(novel.minor_characters())
        self.chartViewGenderMinor.setChart(self._chartGenderMinor)

        self._chartAge = PolarBaseChart()
        self.chartViewAge.setChart(self._chartAge)

    @overrides
    def display(self):
        pass


class PovDistributionChart(BaseChart):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.createDefaultAxes()
        self.setTitle("POV Distribution")

        self.pov_number = {}
        self._acts_filter = {1: True, 2: True, 3: True}

    def toggleAct(self, act: int, toggled: bool):
        self._acts_filter[act] = toggled
        self.refresh()

    def refresh(self, novel: Novel):
        for k in self.pov_number.keys():
            self.pov_number[k] = 0

        for scene in novel.scenes:
            if not self._acts_filter[acts_registry.act(scene)]:
                continue
            if scene.pov and scene.pov.name not in self.pov_number.keys():
                self.pov_number[scene.pov.name] = 0
            if scene.pov:
                self.pov_number[scene.pov.name] += 1

        series = QPieSeries()
        for k, v in self.pov_number.items():
            if v:
                slice = series.append(k, v)
                slice.setLabelVisible()

        for slice in series.slices():
            slice.setLabel(slice.label() + " {:.1f}%".format(100 * slice.percentage()))

        self.removeAllSeries()
        self.addSeries(series)


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

        self.display()

    @overrides
    def display(self):
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
