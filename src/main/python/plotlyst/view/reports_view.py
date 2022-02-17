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

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.events import CharacterChangedEvent, SceneChangedEvent, SceneDeletedEvent, \
    PlotCreatedEvent
from src.main.python.plotlyst.model.report import ReportsTreeModel, CharacterReportNode, CharacterArcReportNode
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.reports_view_ui import Ui_ReportsView
from src.main.python.plotlyst.view.layout import clear_layout
from src.main.python.plotlyst.view.report.character import CharacterReport, CharacterArcReport


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

        # self.pov_number = {}

        # self.chart = QChart()
        # self.chart.legend().hide()
        # self._update_characters_chart()
        # self.chart.createDefaultAxes()
        # self.chart.setAnimationOptions(QChart.SeriesAnimations)
        # self.chart.setTitle("POV Distribution")

        # chartview = QChartView(self.chart)
        # chartview.setRenderHint(QPainter.Antialiasing)

        # self.ui.tabCharacterSceneDistribution.layout().addWidget(chartview)
        #
        # self.ui.tabWidget.setCurrentIndex(3)
        #
        # self.storylines_distribution = StorylinesDistribution(self.novel)
        # self.ui.tabStoryDistribution.layout().addWidget(self.storylines_distribution)
        #
        # self.scenes_model = ScenesTableModel(self.novel)
        # self._scenes_proxy = ScenesFilterProxyModel()
        # self._scenes_proxy.setSourceModel(self.scenes_model)
        # self._scenes_proxy.setEmptyPovFilter(True)
        #
        # for pov in self.novel.pov_characters():
        #     self._scenes_proxy.setCharacterFilter(pov, False)
        #
        # self.ui.tblScenes.setModel(self._scenes_proxy)
        # for col in range(self.scenes_model.columnCount()):
        #     self.ui.tblScenes.hideColumn(col)
        # self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColTitle, QHeaderView.Stretch)
        # self.ui.tblScenes.showColumn(ScenesTableModel.ColTitle)
        # self.ui.tblScenes.showColumn(ScenesTableModel.ColArc)
        # self.ui.tblScenes.setItemDelegate(ScenesViewDelegate())
        #
        # self.arc_chart_view = CharacterArc(self.novel)
        #
        # self._arc_character: Optional[Character] = None
        # self._characters_selector = CharacterSelectorWidget()
        # self._characters_selector.characterToggled.connect(self._arc_character_toggled)
        # self._update_characters_selectors()
        # self.ui.tabCharacterArcs.layout().insertWidget(0, self._characters_selector)
        # self.ui.wdgArc.layout().addWidget(self.arc_chart_view)
        #
        # self.scenes_model.valueChanged.connect(lambda: self.arc_chart_view.refresh(self._arc_character))

    @overrides
    def refresh(self):
        pass

    def _reportClicked(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageReport)
        clear_layout(self.ui.wdgReportContainer.layout())

        index = self.ui.treeReports.selectedIndexes()[0]
        node = index.data(ReportsTreeModel.NodeRole)
        if isinstance(node, CharacterReportNode):
            report = CharacterReport(self.novel, self.ui.wdgReportContainer)
        elif isinstance(node, CharacterArcReportNode):
            report = CharacterArcReport(self.novel, self.ui.wdgReportContainer)
        else:
            return

        self.ui.wdgReportContainer.layout().addWidget(report)

    # def _update_characters_selectors(self):
    #     pov_chars = []
    #     for scene in self.novel.scenes:
    #         if scene.pov and scene.pov not in pov_chars:
    #             pov_chars.append(scene.pov)
    #     self._characters_selector.setCharacters(pov_chars)
    #
    # def _arc_character_toggled(self, character: Character):
    #     self._arc_character = character
    #     for pov in self.novel.pov_characters():
    #         self._scenes_proxy.setCharacterFilter(pov, False)
    #     if self.novel.characters:
    #         self._scenes_proxy.setCharacterFilter(character, True)
    #     self.arc_chart_view.refresh(self._arc_character)

    # def _update_characters_chart(self):
    # for k in self.pov_number.keys():
    #     self.pov_number[k] = 0
    #
    # include_act1 = self.ui.btnAct1.isChecked()
    # include_act2 = self.ui.btnAct2.isChecked()
    # include_act3 = self.ui.btnAct3.isChecked()
    # in_act_2 = False
    # in_act_3 = False
    # for scene in self.novel.scenes:
    #     if (include_act1 and not in_act_2) or (include_act2 and in_act_2) or (include_act3 and in_act_3):
    #         if scene.pov and scene.pov.name not in self.pov_number.keys():
    #             self.pov_number[scene.pov.name] = 0
    #         if scene.pov:
    #             self.pov_number[scene.pov.name] += 1
    #
    #     if scene.beat and scene.beat.act == 1 and scene.beat.ends_act:
    #         in_act_2 = True
    #     elif scene.beat and scene.beat.act == 2 and scene.beat.ends_act:
    #         in_act_3 = True
    #
    # series = QPieSeries()
    # for k, v in self.pov_number.items():
    #     if v:
    #         slice = series.append(k, v)
    #         slice.setLabelVisible(True)
    #
    # for slice in series.slices():
    #     slice.setLabel(slice.label() + " {:.1f}%".format(100 * slice.percentage()))
    #
    # self.chart.removeAllSeries()
    # self.chart.addSeries(series)
