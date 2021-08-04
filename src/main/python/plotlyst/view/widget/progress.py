"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from typing import List

from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter

from src.main.python.plotlyst.core.domain import Novel


# class ProgressCharts(QWidget):
#
#     def __init__(self, number_of_charts: int, parent=None):
#         super(ProgressCharts, self).__init__(parent)
#         self._layout = QHBoxLayout()
#         self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
#         self.setLayout(self._layout)
#
#         self.charts: List[QChart] = []
#         for _ in range(number_of_charts):
#             chart = QChart()
#             chart.legend().hide()
#             chart.setAnimationOptions(QChart.SeriesAnimations)
#
#             chartview = QChartView(chart)
#             chartview.setMaximumHeight(250)
#             chartview.setRenderHint(QPainter.Antialiasing)
#
#             self._layout.addWidget(chartview)
#             self.charts.append(chart)
#
#     def refresh(self, values: List[Tuple[int, int]]):
#         for i, value in enumerate(values):
#             self.charts[i].removeAllSeries()
#
#             series = QPieSeries()
#             series.setHoleSize(0.45)
#             percentage_slice = QPieSlice('Progress', value[0])
#             percentage_slice.setColor(Qt.darkBlue)
#             empty_slice = QPieSlice('', value[1] - value[0])
#             empty_slice.setColor(Qt.white)
#             series.append(percentage_slice)
#             series.append(empty_slice)
#             if i == 0:
#                 title = "Overall:"
#             else:
#                 title = f'Act {i}:'
#             self.charts[i].setTitle(title + " {:.1f}%".format(100 * percentage_slice.percentage()))
#
#             self.charts[i].addSeries(series)


class ProgressChartView(QChartView):
    def __init__(self, value: int, max: int, title_prefix: str = 'Progress', parent=None):
        super(ProgressChartView, self).__init__(parent)
        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)

        self.setChart(self.chart)
        self.setMaximumHeight(150)
        self.setMaximumWidth(250)
        self.setRenderHint(QPainter.Antialiasing)

        self.refresh(value, max, title_prefix)

    def refresh(self, value: int, max: int, title_prefix: str = 'Progress'):
        self.chart.removeAllSeries()
        series = QPieSeries()
        series.setHoleSize(0.45)
        percentage_slice = QPieSlice('Progress', value)
        percentage_slice.setColor(Qt.darkBlue)
        empty_slice = QPieSlice('', max - value)
        empty_slice.setColor(Qt.white)
        series.append(percentage_slice)
        series.append(empty_slice)
        self.chart.setTitle(title_prefix + " {:.1f}%".format(100 * percentage_slice.percentage()))

        self.chart.addSeries(series)


class SceneStageProgressCharts:

    def __init__(self, novel: Novel):
        self.novel = novel
        self._chartviews: List[ProgressChartView] = []
        self._stage = self.novel.stages[1]  # first draft
        self._stage_index = 1

    def charts(self) -> List[ProgressChartView]:
        return self._chartviews

    def refresh(self):
        in_act_1 = True
        in_act_2 = False
        in_act_3 = False
        act1: List[bool] = []
        act2: List[bool] = []
        act3: List[bool] = []

        for scene in self.novel.scenes:
            if scene.pivotal == 'First plot point':
                in_act_2 = True
                in_act_1 = False
            elif scene.pivotal == 'Dark moment':
                in_act_3 = True
                in_act_2 = False
            if scene.stage and self.novel.stages.index(scene.stage) >= self._stage_index:
                match = True
            else:
                match = False
            if in_act_1:
                act1.append(match)
            elif in_act_2:
                act2.append(match)
            elif in_act_3:
                act3.append(match)

        values = []
        match_in_act1 = len([x for x in act1 if x])
        match_in_act2 = len([x for x in act2 if x])
        match_in_act3 = len([x for x in act3 if x])

        values.append((match_in_act1 + match_in_act2 + match_in_act3, len(self.novel.scenes)))

        if act1:
            values.append((match_in_act1, len(act1)))
        else:
            values.append((0, 1))
        if act2:
            values.append((match_in_act2, len(act2)))
        else:
            values.append((0, 1))
        if act3:
            values.append((match_in_act3, len(act3)))
        else:
            values.append((0, 1))

        if not self._chartviews:
            for v in values:
                view = ProgressChartView(v[0], v[1])
                self._chartviews.append(view)
        else:
            for i, v in enumerate(values):
                self._chartviews[i].refresh(v[0], v[1])
