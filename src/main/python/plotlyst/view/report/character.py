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
from typing import Optional

from PyQt5.QtChart import QChart, QPieSeries
from PyQt5.QtChart import QValueAxis, QSplineSeries
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QWidget, QToolButton
from overrides import overrides
from qthandy import clear_layout, vspacer, hbox, transparent, vbox

from src.main.python.plotlyst.core.domain import Novel, Character, Scene
from src.main.python.plotlyst.view.generated.report.character_arc_report_ui import Ui_CharacterArcReport
from src.main.python.plotlyst.view.generated.report.character_report_ui import Ui_CharacterReport
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.report import AbstractReport
from src.main.python.plotlyst.view.widget.characters import CharacterEmotionButton


class CharacterReport(AbstractReport, Ui_CharacterReport):

    def __init__(self, novel: Novel, parent=None):
        super(CharacterReport, self).__init__(novel, parent)

        self.btnAct1.setIcon(IconRegistry.act_one_icon())
        self.btnAct2.setIcon(IconRegistry.act_two_icon())
        self.btnAct3.setIcon(IconRegistry.act_three_icon())
        self.btnAct1.toggled.connect(self._updateCharactersChart)
        self.btnAct2.toggled.connect(self._updateCharactersChart)
        self.btnAct3.toggled.connect(self._updateCharactersChart)

        self.pov_number = {}

        self.chart = QChart()
        self.chart.legend().hide()
        self._updateCharactersChart()
        self.chart.createDefaultAxes()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setTitle("POV Distribution")

        self.chartView.setChart(self.chart)

    @overrides
    def display(self):
        pass

    def _updateCharactersChart(self):
        for k in self.pov_number.keys():
            self.pov_number[k] = 0

        include_act1 = self.btnAct1.isChecked()
        include_act2 = self.btnAct2.isChecked()
        include_act3 = self.btnAct3.isChecked()
        in_act_2 = False
        in_act_3 = False
        for scene in self.novel.scenes:
            if (include_act1 and not in_act_2) or (include_act2 and in_act_2) or (include_act3 and in_act_3):
                if scene.pov and scene.pov.name not in self.pov_number.keys():
                    self.pov_number[scene.pov.name] = 0
                if scene.pov:
                    self.pov_number[scene.pov.name] += 1

            beat = scene.beat(self.novel)
            if beat and beat.act == 1 and beat.ends_act:
                in_act_2 = True
            elif beat and beat.act == 2 and beat.ends_act:
                in_act_3 = True

        series = QPieSeries()
        for k, v in self.pov_number.items():
            if v:
                slice = series.append(k, v)
                slice.setLabelVisible(True)

        for slice in series.slices():
            slice.setLabel(slice.label() + " {:.1f}%".format(100 * slice.percentage()))

        self.chart.removeAllSeries()
        self.chart.addSeries(series)


class SceneArcWidget(QWidget):
    arcChanged = pyqtSignal(Scene)

    def __init__(self, scene: Scene, novel: Novel, parent=None):
        super(SceneArcWidget, self).__init__(parent)
        hbox(self, 0, 2)

        self.scene = scene

        self.btnSceneType = QToolButton()
        transparent(self.btnSceneType)
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


class CharacterArcChart(QChart):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.createDefaultAxes()
        self.legend().hide()
        self.setAnimationOptions(QChart.SeriesAnimations)
        self.setAnimationDuration(500)
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

        points = series.pointsVector()
        if not points:
            return

        min_ = min([x.y() for x in points])
        max_ = max([x.y() for x in points])
        limit = max(abs(min_), max_)
        self.axis = QValueAxis()
        self.axis.setRange(-limit - 3, limit + 3)
        self.addSeries(series)
        self.setAxisY(self.axis, series)
        self.axis.setVisible(False)

# class StorylinesDistribution(QChartView):
#     def __init__(self, novel: Novel, parent=None):
#         super().__init__(parent)
#         self.novel = novel
#         arc_chart = QChart()
#         arc_chart.createDefaultAxes()
#         arc_chart.setAnimationOptions(QChart.SeriesAnimations)
#         arc_chart.setTitle('Storylines and characters distribution')
#         self.setChart(arc_chart)
#         self.setRenderHint(QPainter.Antialiasing)
#         self.axis: Optional[QBarCategoryAxis] = None
#
#         self.refresh()
#
#     def refresh(self):
#         self.chart().removeAllSeries()
#         if self.axis:
#             self.chart().removeAxis(self.axis)
#
#         character_names = [x.name for x in self.novel.characters]
#         series = QStackedBarSeries()
#         for i, plot in enumerate(self.novel.plots):
#             set = QBarSet(plot.text)
#             set.setColor(QColor(plot.color_hexa))
#             occurences = []
#             for char in self.novel.characters:
#                 v = 0
#                 for scene in self.novel.scenes:
#                     if plot in scene.plots():
#                         if char == scene.pov or char in scene.characters:
#                             v += 1
#                 occurences.append(v)
#                 set.append(v)
#             series.append(set)
#         self.axis = QBarCategoryAxis()
#         self.axis.append(character_names)
#         self.chart().addAxis(self.axis, Qt.AlignBottom)
#         series.attachAxis(self.axis)
#         self.chart().addSeries(series)
