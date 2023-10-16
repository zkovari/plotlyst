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
from typing import List, Dict

import qtanim
from PyQt6.QtCharts import QSplineSeries, QValueAxis, QLegend
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen, QColor, QShowEvent
from overrides import overrides
from qthandy import clear_layout, vspacer, bold, gc

from src.main.python.plotlyst.core.domain import Novel, Plot
from src.main.python.plotlyst.view.common import icon_to_html_img
from src.main.python.plotlyst.view.generated.report.plot_report_ui import Ui_PlotReport
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.report import AbstractReport
from src.main.python.plotlyst.view.widget.button import EyeToggle
from src.main.python.plotlyst.view.widget.chart import BaseChart
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode


class PlotArcNode(ContainerNode):
    plotToggled = pyqtSignal(Plot, bool)

    def __init__(self, plot: Plot, parent=None):
        super(PlotArcNode, self).__init__(plot.text, parent)
        self._plot = plot

        self.setPlusButtonEnabled(False)
        self.setMenuEnabled(False)
        self.setSelectionEnabled(False)

        self._btnVisible = EyeToggle()
        self._btnVisible.setToolTip('Toggle arc')
        self._btnVisible.toggled.connect(self._toggled)
        self._wdgTitle.layout().addWidget(self._btnVisible)

        self.refresh()

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        self.refresh()

    def refresh(self):
        self._lblTitle.setText(self._plot.text)
        if self._plot.icon:
            self._icon.setIcon(IconRegistry.from_name(self._plot.icon, self._plot.icon_color))
            self._icon.setVisible(True)
        else:
            self._icon.setHidden(True)

    def isToggled(self):
        return self._btnVisible.isChecked()

    def _toggled(self, toggled: bool):
        bold(self._lblTitle, toggled)
        self.plotToggled.emit(self._plot, toggled)


class ArcsTreeView(TreeView):
    storylineToggled = pyqtSignal(Plot, bool)

    def __init__(self, novel: Novel, parent=None):
        super(ArcsTreeView, self).__init__(parent)
        self._novel = novel
        self._centralWidget.setProperty('relaxed-white-bg', True)

        self._storylineNodes: Dict[Plot, PlotArcNode] = {}
        self._storylinesNode = ContainerNode('Storylines', IconRegistry.storylines_icon(color='grey'), readOnly=True)

    def refresh(self):
        clear_layout(self._centralWidget, auto_delete=False)

        for plot in self._novel.plots:
            if plot not in self._storylineNodes.keys():
                node = PlotArcNode(plot)
                self._storylineNodes[plot] = node
                node.plotToggled.connect(self.storylineToggled.emit)
                self._storylinesNode.addChild(node)

        self._centralWidget.layout().addWidget(self._storylinesNode)
        self._centralWidget.layout().addWidget(vspacer())

    def removeStoryline(self, plot: Plot):
        node = self._storylineNodes.pop(plot)
        if node.isToggled():
            self.storylineToggled.emit(plot, False)
        gc(node)


class ArcReport(AbstractReport, Ui_PlotReport):

    def __init__(self, novel: Novel, parent=None):
        super(ArcReport, self).__init__(novel, parent)

        self.chartValues = StoryArcChart(self.novel)
        self.chartViewPlotValues.setChart(self.chartValues)
        self._treeView = ArcsTreeView(novel)
        self._treeView.storylineToggled.connect(self._plotToggled)
        self.wdgTreeParent.layout().addWidget(self._treeView)
        self.splitter.setSizes([150, 500])

        self.btnArcsToggle.setIcon(IconRegistry.from_name('mdi.file-tree-outline'))
        self.btnArcsToggle.clicked.connect(self._arcsSelectorClicked)

        self.refresh()

    @overrides
    def refresh(self):
        self._treeView.refresh()

    def removeStoryline(self, plot: Plot):
        self._treeView.removeStoryline(plot)

    def _arcsSelectorClicked(self, toggled: bool):
        qtanim.toggle_expansion(self.wdgTreeParent, toggled)

    def _plotToggled(self, plot: Plot, toggled: bool):
        self.chartValues.setStorylineVisible(plot, toggled)


class StoryArcChart(BaseChart):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.createDefaultAxes()
        self.legend().setMarkerShape(QLegend.MarkerShape.MarkerShapeCircle)
        self.legend().show()

        self._plots: List[Plot] = []

        self.setTitle('Story arc')

    def setStorylineVisible(self, plot: Plot, visible: bool):
        if visible:
            self._plots.append(plot)
        else:
            self._plots.remove(plot)

        self.refresh()

    def refresh(self):
        self.reset()

        axisX = QValueAxis()
        axisX.setRange(0, len(self.novel.scenes))
        self.addAxis(axisX, Qt.AlignmentFlag.AlignBottom)
        axisX.setVisible(False)

        axisY = QValueAxis()
        self.addAxis(axisY, Qt.AlignmentFlag.AlignLeft)

        min_ = 0
        max_ = 0
        for plot in self._plots:
            for value in plot.values:
                charge = 0
                series = QSplineSeries()
                series.setName(icon_to_html_img(IconRegistry.from_name(value.icon, value.icon_color)) + value.text)
                pen = QPen()
                pen.setColor(QColor(value.icon_color))
                pen.setWidth(2)
                series.setPen(pen)
                series.append(0, charge)

                for i, scene in enumerate(self.novel.scenes):
                    for scene_ref in scene.plot_values:
                        if scene_ref.plot.id != plot.id:
                            continue
                        for scene_p_value in scene_ref.data.values:
                            if scene_p_value.plot_value_id == value.id:
                                charge += scene_p_value.charge
                                series.append(i + 1, charge)

                points = series.points()
                min_ = min(min([x.y() for x in points]), min_)
                max_ = max(max([x.y() for x in points]), max_)

                self.addSeries(series)
                series.attachAxis(axisY)

        limit = max(abs(min_), max_)
        axisY.setRange(-limit - 1, limit + 1)
        axisY.setVisible(False)
