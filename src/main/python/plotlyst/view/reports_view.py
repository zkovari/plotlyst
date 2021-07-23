"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
import numpy as np
from PyQt5.QtChart import QPieSeries, QChart, QChartView
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QHeaderView
from matplotlib import ticker
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from overrides import overrides

from src.main.python.plotlyst.core.client import client
from src.main.python.plotlyst.core.domain import Novel, Scene, Character
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.model.events import NovelReloadedEvent
from src.main.python.plotlyst.model.novel import NovelStoryLinesListModel
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel, ScenesFilterProxyModel
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.reports_view_ui import Ui_ReportsView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.scenes_view import ScenesViewDelegate


class ReportsView(AbstractNovelView):
    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.ui = Ui_ReportsView()
        self.ui.setupUi(self.widget)
        self.scene_selected = None

        self.ui.storyLinesMap.setNovel(novel)
        self.ui.storyLinesMap.scene_selected.connect(self._on_scene_selected)
        self.ui.btnAct1.setIcon(IconRegistry.act_one_icon())
        self.ui.btnAct2.setIcon(IconRegistry.act_two_icon())
        self.ui.btnAct3.setIcon(IconRegistry.act_three_icon())
        self.ui.btnAct1.toggled.connect(self._update_characters_chart)
        self.ui.btnAct2.toggled.connect(self._update_characters_chart)
        self.ui.btnAct3.toggled.connect(self._update_characters_chart)

        self.pov_number = {}

        self.chart = QChart()
        self.chart.legend().hide()
        self._update_characters_chart()
        self.chart.createDefaultAxes()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setTitle("POV Distribution")

        chartview = QChartView(self.chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        self.ui.tabCharacterSceneDistribution.layout().addWidget(chartview)

        self.ui.tabWidget.setCurrentIndex(3)
        self.story_line_model = NovelStoryLinesListModel(self.novel)
        self.story_line_model.selection_changed.connect(self._story_line_selection_changed)
        self.ui.listView.setModel(self.story_line_model)

        self.story_lines_canvas = StoryLinesCanvas(self.novel, parent=self)
        toolbar = NavigationToolbar(self.story_lines_canvas, self.ui.tabStoryDistribution)
        self.ui.tabStoryDistribution.layout().addWidget(toolbar)
        self.ui.tabStoryDistribution.layout().addWidget(self.story_lines_canvas)

        self.scenes_model = ScenesTableModel(self.novel)
        self._scenes_proxy = ScenesFilterProxyModel()
        self._scenes_proxy.setSourceModel(self.scenes_model)
        povs = set([x.pov for x in self.novel.scenes])
        for pov in povs:
            self._scenes_proxy.setCharacterFilter(pov, False)
        if self.novel.characters:
            self._scenes_proxy.setCharacterFilter(self.novel.characters[0], True)

        self.ui.tblScenes.setModel(self._scenes_proxy)
        for col in range(self.scenes_model.columnCount()):
            self.ui.tblScenes.hideColumn(col)
        self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColTitle, QHeaderView.Stretch)
        self.ui.tblScenes.showColumn(ScenesTableModel.ColTitle)
        self.ui.tblScenes.showColumn(ScenesTableModel.ColArc)
        self.ui.tblScenes.setItemDelegate(ScenesViewDelegate())
        if self.novel.characters:
            self.arc_canvas = CharacterArcCanvas(self.novel, self.novel.characters[0], parent=self)
            self.ui.tabCharacterArcs.layout().addWidget(self.arc_canvas)

            self.scenes_model.valueChanged.connect(self.arc_canvas.refresh_plot)

        event_dispatcher.register(self, NovelReloadedEvent)

    @overrides
    def refresh(self):
        self._update_characters_chart()
        self.story_lines_canvas.refresh_plot()

    def _on_scene_selected(self, scene: Scene):
        self.scene_selected = scene
        self.ui.lineEdit.setText(scene.title)
        self.story_line_model.selected.clear()
        for story_line in scene.story_lines:
            self.story_line_model.selected.add(story_line)
        self.story_line_model.modelReset.emit()

    def _story_line_selection_changed(self):
        if not self.scene_selected:
            return
        self.scene_selected.story_lines.clear()
        for story_line in self.story_line_model.selected:
            self.scene_selected.story_lines.append(story_line)

        client.update_scene(self.scene_selected)
        self.ui.storyLinesMap.update()

    def _update_characters_chart(self):
        for k in self.pov_number.keys():
            self.pov_number[k] = 0

        include_act1 = self.ui.btnAct1.isChecked()
        include_act2 = self.ui.btnAct2.isChecked()
        include_act3 = self.ui.btnAct3.isChecked()
        in_act_2 = False
        in_act_3 = False
        for scene in self.novel.scenes:
            if (include_act1 and not in_act_2) or (include_act2 and in_act_2) or (include_act3 and in_act_3):
                if scene.pov and scene.pov.name not in self.pov_number.keys():
                    self.pov_number[scene.pov.name] = 0
                if scene.pov:
                    self.pov_number[scene.pov.name] += 1

            if scene.pivotal == 'First plot point':
                in_act_2 = True
            elif scene.pivotal == 'Dark moment':
                in_act_3 = True

        series = QPieSeries()
        for k, v in self.pov_number.items():
            if v:
                slice = series.append(k, v)
                slice.setLabelVisible(True)

        for slice in series.slices():
            slice.setLabel(slice.label() + " {:.1f}%".format(100 * slice.percentage()))

        self.chart.removeAllSeries()
        self.chart.addSeries(series)


class StoryLinesCanvas(FigureCanvasQTAgg):

    def __init__(self, novel: Novel, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = None
        self.novel = novel

        super().__init__(self.fig)
        self.refresh_plot()

    def refresh_plot(self):
        if self.axes:
            self.fig.clear()

        self.axes = self.fig.add_subplot(111)

        character_names = [x.name for x in self.novel.characters]
        width = 0.35  # the width of the bars: can also be len(x) sequence

        bottoms = None
        for i, story_line in enumerate(self.novel.story_lines):
            occurences = []
            for char in self.novel.characters:
                v = 0
                for scene in self.novel.scenes:
                    if story_line in scene.story_lines:
                        if char == scene.pov or char in scene.characters:
                            v += 1
                occurences.append(v)
            if bottoms is None:
                self.axes.bar(character_names, occurences, width, label=story_line.text, color=story_line.color_hexa)
                bottoms = np.array(occurences)
            else:
                self.axes.bar(character_names, occurences, width, label=story_line.text, bottom=bottoms,
                              color=story_line.color_hexa)
                bottoms += np.array(occurences)

        self.axes.set_ylabel('# of scenes')
        self.axes.set_title('Story lines and characters distribution')
        self.axes.legend()

        self.draw()


class CharacterArcCanvas(FigureCanvasQTAgg):
    def __init__(self, novel: Novel, character: Character, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.novel = novel
        self.character = character
        self.axes = None

        super().__init__(self.fig)
        self.refresh_plot()

    def refresh_plot(self):
        if self.axes:
            self.fig.clear()

        self.axes = self.fig.add_subplot(111)

        x = np.arange(0, len([x for x in self.novel.scenes if x.pov == self.character]))
        arc_value: int = 0
        y = []
        for scene in self.novel.scenes:
            if scene.pov != self.character:
                continue
            for arc in scene.arcs:
                if arc.character == self.character:
                    arc_value += arc.arc
            y.append(arc_value)

        self.axes.plot(x, y)
        if y:
            min_y = min(y)
            max_y = max(y)
        else:
            min_y = -10
            max_y = 10

        if min_y < 0 and abs(min_y) > max_y:
            self.axes.set_ylim([min_y - 3, abs(min_y) + 3])
        self.axes.yaxis.set_major_locator(ticker.NullLocator())
        self.axes.set(xlabel='Scenes', ylabel='Arc',
                      title=f'Character arc for {self.character.name}')

        self.draw()
