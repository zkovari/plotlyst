"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
from PyQt6.QtCharts import QValueAxis, QBarSeries, QBarSet
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from overrides import overrides

from plotlyst.core.domain import Novel
from plotlyst.core.text import html
from plotlyst.view.generated.report.world_building_report_ui import Ui_WorldBuildingReport
from plotlyst.view.report import AbstractReport
from plotlyst.view.widget.chart import BaseChart


class WorldBuildingReport(AbstractReport, Ui_WorldBuildingReport):
    def __init__(self, novel: Novel, parent=None):
        super(WorldBuildingReport, self).__init__(novel, parent)

        self.chartWorldBuilding = WorldBuildingRevelationChart(self.novel)
        self.chartViewWorldBuilding.setChart(self.chartWorldBuilding)
        self.display()

    @overrides
    def display(self):
        self.chartWorldBuilding.refresh()


class WorldBuildingRevelationChart(BaseChart):
    def __init__(self, novel: Novel, parent=None):
        super(WorldBuildingRevelationChart, self).__init__(parent)
        self.novel = novel
        self.setTitle(html('World building').bold())

    def refresh(self):
        self.reset()

        axisX = QValueAxis()
        axisX.setRange(0, len(self.novel.scenes))
        self.addAxis(axisX, Qt.AlignmentFlag.AlignBottom)
        axisX.setVisible(False)

        axisY = QValueAxis()
        axisY.setRange(0, 5)
        self.addAxis(axisY, Qt.AlignmentFlag.AlignLeft)
        axisY.setVisible(False)

        set_ = QBarSet('World')
        set_.setColor(QColor('#40916c'))

        for scene in self.novel.scenes:
            set_.append(scene.drive.worldbuilding)

        series = QBarSeries()
        series.append(set_)

        self.addSeries(series)
        series.attachAxis(axisX)
        series.attachAxis(axisY)
