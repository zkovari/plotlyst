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

from PyQt5.QtChart import QChart, QChartView, QBarSet, QStackedBarSeries, \
    QBarCategoryAxis, QPieSeries
from PyQt5.QtChart import QValueAxis, QSplineSeries
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, Character
from src.main.python.plotlyst.view.generated.report.character_report_ui import Ui_CharacterReport
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.report import AbstractReport


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

            if scene.beat and scene.beat.act == 1 and scene.beat.ends_act:
                in_act_2 = True
            elif scene.beat and scene.beat.act == 2 and scene.beat.ends_act:
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


class CharacterArc(QChartView):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        arc_chart = QChart()
        arc_chart.createDefaultAxes()
        arc_chart.legend().hide()
        arc_chart.setAnimationOptions(QChart.AllAnimations)
        self.setChart(arc_chart)
        self.setRenderHint(QPainter.Antialiasing)
        self.axis: Optional[QValueAxis] = None

    def refresh(self, character: Character):
        self.chart().removeAllSeries()
        if self.axis:
            self.chart().removeAxis(self.axis)
        self.chart().setTitle(f'Character arc for {character.name}')

        series = QSplineSeries()
        arc_value: int = 0
        series.append(0, 0)
        for scene in self.novel.scenes:
            if scene.pov != character:
                continue
            for arc in scene.arcs:
                if arc.character.id == character.id:
                    arc_value += arc.arc
                    series.append(len(series), arc_value)

        points = series.pointsVector()
        if not points:
            return

        min_ = min([x.y() for x in points])
        max_ = max([x.y() for x in points])
        limit = max(abs(min_), max_)
        self.axis = QValueAxis()
        self.axis.setRange(-limit - 3, limit + 3)
        self.chart().addSeries(series)
        self.chart().setAxisY(self.axis, series)
        self.axis.setVisible(False)


class StorylinesDistribution(QChartView):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        arc_chart = QChart()
        arc_chart.createDefaultAxes()
        arc_chart.setAnimationOptions(QChart.SeriesAnimations)
        arc_chart.setTitle('Storylines and characters distribution')
        self.setChart(arc_chart)
        self.setRenderHint(QPainter.Antialiasing)
        self.axis: Optional[QBarCategoryAxis] = None

        self.refresh()

    def refresh(self):
        self.chart().removeAllSeries()
        if self.axis:
            self.chart().removeAxis(self.axis)

        character_names = [x.name for x in self.novel.characters]
        series = QStackedBarSeries()
        for i, plot in enumerate(self.novel.plots):
            set = QBarSet(plot.text)
            set.setColor(QColor(plot.color_hexa))
            occurences = []
            for char in self.novel.characters:
                v = 0
                for scene in self.novel.scenes:
                    if plot in scene.plots():
                        if char == scene.pov or char in scene.characters:
                            v += 1
                occurences.append(v)
                set.append(v)
            series.append(set)
        self.axis = QBarCategoryAxis()
        self.axis.append(character_names)
        self.chart().addAxis(self.axis, Qt.AlignBottom)
        series.attachAxis(self.axis)
        self.chart().addSeries(series)
