from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view.generated.report.manuscript_report_ui import Ui_ManuscriptReport
from src.main.python.plotlyst.view.report import AbstractReport
from src.main.python.plotlyst.view.widget.chart import ManuscriptLengthChart


class ManuscriptReport(AbstractReport, Ui_ManuscriptReport):

    def __init__(self, novel: Novel, parent=None):
        super(ManuscriptReport, self).__init__(novel, parent)
        self.chart_manuscript = ManuscriptLengthChart()
        self.chartChaptersLength.setChart(self.chart_manuscript)

        self.refresh()

    @overrides
    def refresh(self):
        self.chart_manuscript.refresh(self.novel)
