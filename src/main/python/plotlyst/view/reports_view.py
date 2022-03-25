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

from overrides import overrides
from qthandy import clear_layout

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.events import CharacterChangedEvent, SceneChangedEvent, SceneDeletedEvent, \
    PlotCreatedEvent
from src.main.python.plotlyst.model.report import ReportsTreeModel, CharacterReportNode, CharacterArcReportNode, \
    ConflictReportNode
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.reports_view_ui import Ui_ReportsView
from src.main.python.plotlyst.view.report import AbstractReport
from src.main.python.plotlyst.view.report.character import CharacterReport, CharacterArcReport
from src.main.python.plotlyst.view.report.conflict import ConflictReport


class ReportsView(AbstractNovelView):
    def __init__(self, novel: Novel):
        super().__init__(novel, [CharacterChangedEvent, SceneChangedEvent, SceneDeletedEvent, PlotCreatedEvent])
        self.ui = Ui_ReportsView()
        self.ui.setupUi(self.widget)
        self.scene_selected = None

        self._treeModel = ReportsTreeModel()
        self.ui.treeReports.setModel(self._treeModel)
        self.ui.treeReports.expandAll()
        self.ui.treeReports.clicked.connect(self._reportClicked)

        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEmpty)
        self.ui.splitter.setSizes([100, 500])

    @overrides
    def refresh(self):
        pass

    def displayCharactersReport(self):
        self._displayReport(CharacterReport(self.novel, self.ui.wdgReportContainer))

    def displayArcReport(self):
        self._displayReport(CharacterArcReport(self.novel, self.ui.wdgReportContainer))

    def displayConflictReport(self):
        self._displayReport(ConflictReport(self.novel, self.ui.wdgReportContainer))

    def _displayReport(self, report: AbstractReport):
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageReport)
        clear_layout(self.ui.wdgReportContainer.layout())
        self.ui.wdgReportContainer.layout().addWidget(report)

    def _reportClicked(self):
        index = self.ui.treeReports.selectedIndexes()[0]
        node = index.data(ReportsTreeModel.NodeRole)
        if isinstance(node, CharacterReportNode):
            self.displayCharactersReport()
        elif isinstance(node, CharacterArcReportNode):
            self.displayArcReport()
        elif isinstance(node, ConflictReportNode):
            self.displayConflictReport()
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.pageEmpty)
