from functools import partial
from typing import Optional

from PyQt6.QtCharts import QPieSeries
from overrides import overrides

from plotlyst.core.domain import Novel
from plotlyst.core.text import html
from plotlyst.service.cache import acts_registry
from plotlyst.view.generated.report.scene_report_ui import Ui_SceneReport
from plotlyst.view.icons import IconRegistry
from plotlyst.view.report import AbstractReport
from plotlyst.view.widget.chart import BaseChart, ActDistributionChart


class SceneReport(AbstractReport, Ui_SceneReport):

    def __init__(self, novel: Novel, parent=None):
        super(SceneReport, self).__init__(novel, parent)
        self.btnAct1.setIcon(IconRegistry.act_one_icon())
        self.btnAct2.setIcon(IconRegistry.act_two_icon())
        self.btnAct3.setIcon(IconRegistry.act_three_icon())

        self._povChart = PovDistributionChart()
        self.chartViewPovDistribution.setChart(self._povChart)
        self.btnAct1.toggled.connect(partial(self._povChart.toggleAct, 1))
        self.btnAct2.toggled.connect(partial(self._povChart.toggleAct, 2))
        self.btnAct3.toggled.connect(partial(self._povChart.toggleAct, 3))

        self._actChart = ActDistributionChart()
        self.chartViewActDistribution.setChart(self._actChart)

        self.refresh()

    @overrides
    def refresh(self):
        self._povChart.refresh(self.novel)
        self._actChart.refresh(self.novel)


class PovDistributionChart(BaseChart):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.createDefaultAxes()
        self.setTitle(html("POV Distribution").bold())
        self._novel: Optional[Novel] = None

        self.pov_number = {}
        self._acts_filter = {1: True, 2: True, 3: True}

    def toggleAct(self, act: int, toggled: bool):
        self._acts_filter[act] = toggled
        self.refresh(self._novel)

    def refresh(self, novel: Novel):
        self._novel = novel
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
        series.setHoleSize(0.45)
        for k, v in self.pov_number.items():
            if v:
                slice = series.append(k, v)
                slice.setLabelVisible()

        for slice in series.slices():
            slice.setLabel(slice.label() + " {:.1f}%".format(100 * slice.percentage()))

        self.removeAllSeries()
        self.addSeries(series)
