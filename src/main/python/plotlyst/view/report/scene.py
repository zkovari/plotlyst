from typing import Optional, Dict

from PyQt6.QtCharts import QPieSeries
from PyQt6.QtCore import Qt
from overrides import overrides

from plotlyst.core.domain import Novel, Character
from plotlyst.core.text import html
from plotlyst.service.cache import acts_registry
from plotlyst.view.common import icon_to_html_img
from plotlyst.view.generated.report.scene_report_ui import Ui_SceneReport
from plotlyst.view.icons import avatars
from plotlyst.view.report import AbstractReport
from plotlyst.view.widget.chart import BaseChart, ActDistributionChart
from plotlyst.view.widget.structure.selector import ActSelectorButtons


class SceneReport(AbstractReport, Ui_SceneReport):

    def __init__(self, novel: Novel, parent=None):
        super(SceneReport, self).__init__(novel, parent)
        self._povChart = PovDistributionChart()
        self.chartViewPovDistribution.setChart(self._povChart)
        self.actSelector = ActSelectorButtons(novel)
        self.layoutActButtons.layout().addWidget(self.actSelector, alignment=Qt.AlignmentFlag.AlignCenter)
        self.actSelector.actToggled.connect(self._povChart.toggleAct)

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

        self.pov_number: Dict[Character, int] = {}
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
            if scene.pov and scene.pov not in self.pov_number.keys():
                self.pov_number[scene.pov] = 0
            if scene.pov:
                self.pov_number[scene.pov] += 1

        series = QPieSeries()
        series.setHoleSize(0.45)
        for k, v in self.pov_number.items():
            if v:
                slice = series.append(k.name, v)
                slice.setLabel(icon_to_html_img(avatars.avatar(k)))
                slice.setLabelVisible()

        for slice in series.slices():
            slice.setLabel(slice.label() + " {:.1f}%".format(100 * slice.percentage()))

        self.removeAllSeries()
        self.addSeries(series)
