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

import qtanim
from PyQt5.QtChart import QChartView, QPieSeries, QPieSlice
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPaintEvent, QPen, QPainterPath
from PyQt5.QtWidgets import QWidget, QSizePolicy
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, SceneStage
from src.main.python.plotlyst.service.cache import acts_registry
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.chart import BaseChart


class ProgressChartView(QChartView):
    def __init__(self, value: int, max: int, title_prefix: str = 'Progress', color=Qt.darkBlue, parent=None):
        super(ProgressChartView, self).__init__(parent)
        self.chart = BaseChart()
        font = QFont()
        font.setBold(True)
        self.chart.setTitleFont(font)
        self._title_prefix = title_prefix
        self._color = color

        self.setChart(self.chart)
        self.setMaximumHeight(200)
        self.setMaximumWidth(250)
        self.setRenderHint(QPainter.Antialiasing)

        self.refresh(value, max)

    def refresh(self, value: int, max: int):
        self.chart.removeAllSeries()
        series = QPieSeries()
        series.setHoleSize(0.45)
        percentage_slice = QPieSlice('Progress', value)
        percentage_slice.setColor(QColor(self._color))
        empty_slice = QPieSlice('', max - value)
        empty_slice.setColor(Qt.white)
        series.append(percentage_slice)
        series.append(empty_slice)
        self.chart.setTitle(self._title_prefix + " {:.1f}%".format(100 * percentage_slice.percentage()))

        self.chart.addSeries(series)


class SceneStageProgressCharts:

    def __init__(self, novel: Novel):
        self.novel = novel
        self._chartviews: List[ProgressChartView] = []
        active_stage = self.novel.active_stage
        if active_stage:
            self._stage = active_stage
        elif self.novel.stages:
            self._stage = self.novel.stages[0]
        else:
            self._stage = None
        self._act_colors = {1: '#02bcd4', 2: '#1bbc9c', 3: '#ff7800'}

    def charts(self) -> List[ProgressChartView]:
        return self._chartviews

    def stage(self) -> SceneStage:
        return self._stage

    def setStage(self, stage: SceneStage):
        self._stage = stage
        self.refresh()

    def refresh(self):
        acts: Dict[int, List[bool]] = {1: [], 2: [], 3: []}
        active_stage_index = self.novel.stages.index(self._stage)

        for scene in self.novel.scenes:
            if scene.stage and self.novel.stages.index(scene.stage) >= active_stage_index:
                acts[acts_registry.act(scene)].append(True)
            else:
                acts[acts_registry.act(scene)].append(False)

        values = []
        all_matches = 0
        for act in [1, 2, 3]:
            matches = len([x for x in acts[act] if x])
            all_matches += matches
            values.append((matches, len(acts[act])))

        values.insert(0, (all_matches, len(self.novel.scenes)))

        if not self._chartviews:
            overall = ProgressChartView(values[0][0], values[0][1], 'Overall:')
            self._chartviews.append(overall)

            for i in range(1, 4):
                act = ProgressChartView(values[i][0], values[i][1], f'Act {i}:',
                                        color=self._act_colors.get(i, Qt.darkBlue))
                self._chartviews.append(act)
        else:
            for i, v in enumerate(values):
                self._chartviews[i].refresh(v[0], v[1])


class CircularProgressBar(QWidget):

    def __init__(self, value: int = 0, maxValue: int = 1, radius: int = 8, parent=None):
        super(CircularProgressBar, self).__init__(parent)
        self._radius: int = radius
        self._penWidth = 2
        self._center = self._radius + self._penWidth
        self._value = value
        self._maxValue = maxValue
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self._tickPixmap = IconRegistry.ok_icon('#2a9d8f').pixmap(self._radius * 2 - 2, self._radius * 2 - 2)

    def value(self) -> int:
        return self._value

    def setValue(self, value: int):
        if value > 0:
            self._value = value if value <= self._maxValue else self._maxValue
        else:
            self._value = 0
        self.update()
        if self._value == self._maxValue and self.isVisible():
            qtanim.glow(self, color=QColor('#2a9d8f'))

    def maxValue(self) -> int:
        return self._maxValue

    def setMaxValue(self, value: int):
        self._maxValue = value

    @overrides
    def sizeHint(self) -> QSize:
        return QSize(self._radius * 2 + self._penWidth * 2, self._radius * 2 + self._penWidth * 2)

    @overrides
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 1, Qt.DotLine))
        painter.drawEllipse(QPoint(self._center, self._center), self._radius, self._radius)

        path = QPainterPath()
        path.moveTo(self._center, self._penWidth)
        path.arcTo(self._penWidth, self._penWidth, self._radius * 2, self._radius * 2, 90,
                   -360 * self._value / self._maxValue)
        painter.setPen(QPen(QColor('#2a9d8f'), self._penWidth, Qt.SolidLine))
        painter.drawPath(path)

        if self._value == self._maxValue:
            painter.drawPixmap(self._penWidth + 1, self._penWidth + 1,
                               self._tickPixmap)

        painter.end()
