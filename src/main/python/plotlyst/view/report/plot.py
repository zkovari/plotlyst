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
from typing import List, Optional

from PyQt5.QtChart import QSplineSeries, QValueAxis
from PyQt5.QtWidgets import QPushButton, QButtonGroup
from overrides import overrides
from qthandy import flow, clear_layout

from src.main.python.plotlyst.core.domain import Novel, Plot
from src.main.python.plotlyst.view.common import pointy
from src.main.python.plotlyst.view.generated.report.plot_report_ui import Ui_PlotReport
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.report import AbstractReport
from src.main.python.plotlyst.view.widget.chart import BaseChart


class _PlotButton(QPushButton):
    def __init__(self, plot: Plot, parent=None):
        super(_PlotButton, self).__init__(parent)
        self.plot = plot

        self.setText(plot.text)
        if plot.icon:
            self.setIcon(IconRegistry.from_name(plot.icon, plot.icon_color))

        self.setCheckable(True)
        pointy(self)


class PlotReport(AbstractReport, Ui_PlotReport):

    def __init__(self, novel: Novel, parent=None):
        super(PlotReport, self).__init__(novel, parent)

        self.chartValues = PlotValuesArcChart(self.novel)
        self.chartViewPlotValues.setChart(self.chartValues)
        flow(self.wdgPlotContainer)
        self._btnGroupPlots: Optional[QButtonGroup] = None

        self.display()

    @overrides
    def display(self):
        clear_layout(self.wdgPlotContainer)
        self._btnGroupPlots = QButtonGroup()
        self._btnGroupPlots.setExclusive(False)

        for plot in self.novel.plots:
            btn = _PlotButton(plot)
            self._btnGroupPlots.addButton(btn)
            self.wdgPlotContainer.layout().addWidget(btn)

        self._btnGroupPlots.buttonToggled.connect(self._plotToggled)

    def _plotToggled(self):
        plots = []
        for btn in self._btnGroupPlots.buttons():
            if btn.isChecked():
                plots.append(btn.plot)

        print(len(plots))

        self.chartValues.refresh(plots)


class PlotValuesArcChart(BaseChart):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.createDefaultAxes()
        self.legend().hide()
        self.axisX: Optional[QValueAxis] = None
        self.axisY: Optional[QValueAxis] = None

        self.setTitle('Plot value charges')

    def refresh(self, plots: List[Plot]):
        self.removeAllSeries()
        if self.axisX:
            self.removeAxis(self.axisX)
        if self.axisY:
            self.removeAxis(self.axisY)

        self.axisX = QValueAxis()
        self.axisX.setRange(0, len(self.novel.scenes))
        self.setAxisX(self.axisX)
        self.axisX.setVisible(False)

        self.axisY = QValueAxis()
        self.setAxisY(self.axisY)

        min_ = 0
        max_ = 0
        for plot in plots:
            print(plot.text)
            for value in plot.values:
                print(value.text)
                charge = 0
                series = QSplineSeries()
                series.append(0, charge)

                for i, scene in enumerate(self.novel.scenes):
                    for scene_ref in scene.plot_values:
                        if scene_ref.plot.id != plot.id:
                            continue
                        for scene_p_value in scene_ref.data.values:
                            if scene_p_value.plot_value_id == value.id:
                                print(f'scene i {i} charge {scene_p_value.charge} overall charge {charge}')
                                charge += scene_p_value.charge
                                series.append(i + 1, charge)

                points = series.pointsVector()
                min_ = min(min([x.y() for x in points]), min_)
                max_ = max(max([x.y() for x in points]), max_)

                self.addSeries(series)
                series.attachAxis(self.axisX)
                series.attachAxis(self.axisY)

        limit = max(abs(min_), max_)

        self.axisY.setRange(-limit - 3, limit + 3)
        self.axisY.setVisible(False)
