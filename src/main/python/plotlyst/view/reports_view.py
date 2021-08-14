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
from typing import Optional

from PyQt5.QtChart import QPieSeries, QChart, QChartView, QValueAxis, QSplineSeries, QBarSet, QStackedBarSeries, \
    QBarCategoryAxis
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QHeaderView
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, Character
from src.main.python.plotlyst.events import CharacterChangedEvent, SceneChangedEvent, SceneDeletedEvent, \
    StorylineCreatedEvent
from src.main.python.plotlyst.model.scenes_model import ScenesTableModel, ScenesFilterProxyModel
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.generated.reports_view_ui import Ui_ReportsView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.scenes_view import ScenesViewDelegate
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorWidget


class ReportsView(AbstractNovelView):
    def __init__(self, novel: Novel):
        super().__init__(novel, [CharacterChangedEvent, SceneChangedEvent, SceneDeletedEvent, StorylineCreatedEvent])
        self.ui = Ui_ReportsView()
        self.ui.setupUi(self.widget)
        self.scene_selected = None

        self.ui.storyLinesMap.setNovel(novel)
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

        self.storylines_distribution = StorylinesDistribution(self.novel)
        self.ui.tabStoryDistribution.layout().addWidget(self.storylines_distribution)

        if not self.novel.story_lines:
            self.ui.stackStoryMap.setCurrentWidget(self.ui.pageInfoStoryMap)

        self.scenes_model = ScenesTableModel(self.novel)
        self._scenes_proxy = ScenesFilterProxyModel()
        self._scenes_proxy.setSourceModel(self.scenes_model)

        for pov in self.novel.pov_characters():
            self._scenes_proxy.setCharacterFilter(pov, False)

        self.ui.tblScenes.setModel(self._scenes_proxy)
        for col in range(self.scenes_model.columnCount()):
            self.ui.tblScenes.hideColumn(col)
        self.ui.tblScenes.horizontalHeader().setSectionResizeMode(ScenesTableModel.ColTitle, QHeaderView.Stretch)
        self.ui.tblScenes.showColumn(ScenesTableModel.ColTitle)
        self.ui.tblScenes.showColumn(ScenesTableModel.ColArc)
        self.ui.tblScenes.setItemDelegate(ScenesViewDelegate())

        self.arc_chart_view = CharacterArc(self.novel)

        self._arc_character: Optional[Character] = None
        self._characters_selector = CharacterSelectorWidget()
        self._characters_selector.characterToggled.connect(self._arc_character_toggled)
        self._update_characters_selectors()
        self.ui.tabCharacterArcs.layout().insertWidget(0, self._characters_selector)
        self.ui.wdgArc.layout().addWidget(self.arc_chart_view)

        self.scenes_model.valueChanged.connect(lambda: self.arc_chart_view.refresh(self._arc_character))

    @overrides
    def refresh(self):
        if self.novel.story_lines:
            self.ui.stackStoryMap.setCurrentWidget(self.ui.pageStoryMap)
        self.scenes_model.modelReset.emit()
        self._update_characters_selectors()
        self._update_characters_chart()
        self.storylines_distribution.refresh()

    def _update_characters_selectors(self):
        pov_chars = []
        for scene in self.novel.scenes:
            if scene.pov and scene.pov not in pov_chars:
                pov_chars.append(scene.pov)
        self._characters_selector.setCharacters(pov_chars)

    def _arc_character_toggled(self, character: Character):
        self._arc_character = character
        for pov in self.novel.pov_characters():
            self._scenes_proxy.setCharacterFilter(pov, False)
        if self.novel.characters:
            self._scenes_proxy.setCharacterFilter(character, True)
        self.arc_chart_view.refresh(self._arc_character)

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

            if scene.beat and scene.beat.act == 1 and scene.beat.ends_act:
                in_act_2 = True
            elif scene.beat and scene.beat.act == 2 and scene.beat.ends_act:
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


class StorylinesDistribution(QChartView):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        arc_chart = QChart()
        arc_chart.createDefaultAxes()
        arc_chart.setAnimationOptions(QChart.SeriesAnimations)
        arc_chart.setTitle('Storylines and characters distribution')
        self.setChart(arc_chart)
        self.setRenderHint(QPainter.Antialiasing)
        self.axis: Optional[QBarCategoryAxis] = None

        self.refresh()

    def refresh(self):
        self.chart().removeAllSeries()
        if self.axis:
            self.chart().removeAxis(self.axis)

        character_names = [x.name for x in self.novel.characters]
        series = QStackedBarSeries()
        for i, story_line in enumerate(self.novel.story_lines):
            set = QBarSet(story_line.text)
            set.setColor(QColor(story_line.color_hexa))
            occurences = []
            for char in self.novel.characters:
                v = 0
                for scene in self.novel.scenes:
                    if story_line in scene.story_lines:
                        if char == scene.pov or char in scene.characters:
                            v += 1
                occurences.append(v)
                set.append(v)
            series.append(set)
        self.axis = QBarCategoryAxis()
        self.axis.append(character_names)
        self.chart().addAxis(self.axis, Qt.AlignBottom)
        series.attachAxis(self.axis)
        self.chart().addSeries(series)


class CharacterArc(QChartView):
    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        arc_chart = QChart()
        arc_chart.createDefaultAxes()
        arc_chart.legend().hide()
        arc_chart.setAnimationOptions(QChart.AllAnimations)
        self.setChart(arc_chart)
        self.setRenderHint(QPainter.Antialiasing)
        self.axis: Optional[QValueAxis] = None

    def refresh(self, character: Character):
        self.chart().removeAllSeries()
        if self.axis:
            self.chart().removeAxis(self.axis)
        self.chart().setTitle(f'Character arc for {character.name}')

        series = QSplineSeries()
        arc_value: int = 0
        series.append(0, 0)
        for scene in self.novel.scenes:
            if scene.pov != character:
                continue
            for arc in scene.arcs:
                if arc.character.id == character.id:
                    arc_value += arc.arc
                    series.append(len(series), arc_value)

        points = series.pointsVector()
        if not points:
            return

        min_ = min([x.y() for x in points])
        max_ = max([x.y() for x in points])
        limit = max(abs(min_), max_)
        self.axis = QValueAxis()
        self.axis.setRange(-limit - 3, limit + 3)
        self.chart().addSeries(series)
        self.chart().setAxisY(self.axis, series)
        self.axis.setVisible(False)
