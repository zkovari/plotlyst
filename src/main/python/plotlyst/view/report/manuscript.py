"""
Plotlyst
Copyright (C) 2021-2025  Zsolt Kovari

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

from overrides import overrides

from plotlyst.core.domain import Novel
from plotlyst.view.generated.report.manuscript_report_ui import Ui_ManuscriptReport
from plotlyst.view.report import AbstractReport
from plotlyst.view.widget.chart import ManuscriptLengthChart


class ManuscriptReport(AbstractReport, Ui_ManuscriptReport):

    def __init__(self, novel: Novel, parent=None):
        super(ManuscriptReport, self).__init__(novel, parent)
        self.chart_manuscript = ManuscriptLengthChart()
        self.chartChaptersLength.setChart(self.chart_manuscript)
        self.cbScenesToggle.toggled.connect(self.setDisplayByScenes)

        self.refresh()

    @overrides
    def refresh(self):
        self.chart_manuscript.refresh(self.novel)

    def setDisplayByScenes(self, display: bool):
        self.chart_manuscript.setDisplayByScenes(display)
        self.chart_manuscript.refresh(self.novel)
