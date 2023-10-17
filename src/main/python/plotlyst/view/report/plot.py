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
from dataclasses import dataclass, field
from functools import partial
from typing import List, Dict, Optional

import qtanim
from PyQt6.QtCharts import QSplineSeries, QValueAxis, QLegend, QAbstractSeries, QLineSeries
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen, QColor, QShowEvent
from overrides import overrides
from qthandy import clear_layout, vspacer, gc

from src.main.python.plotlyst.common import clamp
from src.main.python.plotlyst.core.domain import Novel, Plot, Character
from src.main.python.plotlyst.view.common import icon_to_html_img
from src.main.python.plotlyst.view.generated.report.plot_report_ui import Ui_PlotReport
from src.main.python.plotlyst.view.icons import IconRegistry, avatars
from src.main.python.plotlyst.view.report import AbstractReport
from src.main.python.plotlyst.view.widget.chart import BaseChart
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode, EyeToggleNode


class PlotArcNode(EyeToggleNode):
    plotToggled = pyqtSignal(Plot, bool)

    def __init__(self, plot: Plot, parent=None):
        super(PlotArcNode, self).__init__(plot.text, parent)
        self._plot = plot
        self.setToggleTooltip('Toggle arc')
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

    @overrides
    def _toggled(self, toggled: bool):
        super()._toggled(toggled)
        self.plotToggled.emit(self._plot, toggled)


class ArcsTreeView(TreeView):
    storylineToggled = pyqtSignal(Plot, bool)
    conflictToggled = pyqtSignal(bool)
    characterConflictToggled = pyqtSignal(Character, bool)
    characterEmotionToggled = pyqtSignal(Character, bool)
    characterMotivationToggled = pyqtSignal(Character, bool)

    def __init__(self, novel: Novel, parent=None):
        super(ArcsTreeView, self).__init__(parent)
        self._novel = novel
        self._centralWidget.setProperty('relaxed-white-bg', True)

        self._storylineNodes: Dict[Plot, PlotArcNode] = {}
        self._storylinesNode = ContainerNode('Storylines', IconRegistry.storylines_icon(color='grey'), readOnly=True)

        self._conflictNode = EyeToggleNode('Conflict', IconRegistry.conflict_icon())
        self._conflictNode.setToggleTooltip('Toggle overall conflict intensity')
        self._conflictNode.toggled.connect(self.conflictToggled)

        self._agendaCharactersNode = ContainerNode('Characters', IconRegistry.character_icon('grey'), readOnly=True)

    def refresh(self):
        clear_layout(self._centralWidget, auto_delete=False)
        self._agendaCharactersNode.clearChildren()

        for plot in self._novel.plots:
            if plot not in self._storylineNodes.keys():
                node = PlotArcNode(plot)
                self._storylineNodes[plot] = node
                node.plotToggled.connect(self.storylineToggled.emit)
                self._storylinesNode.addChild(node)

        characters = set()
        for scene in self._novel.scenes:
            if scene.agendas and scene.agendas[0].character_id:
                characters.add(scene.agendas[0].character(self._novel))

        for character in characters:
            self._addCharacterAgendaNodes(character)

        self._centralWidget.layout().addWidget(self._storylinesNode)
        self._centralWidget.layout().addWidget(self._conflictNode)
        self._centralWidget.layout().addWidget(self._agendaCharactersNode)
        self._centralWidget.layout().addWidget(vspacer())

    def removeStoryline(self, plot: Plot):
        node = self._storylineNodes.pop(plot)
        if node.isToggled():
            self.storylineToggled.emit(plot, False)
        gc(node)

    def _addCharacterAgendaNodes(self, character: Character):
        agendaNode = ContainerNode(character.name, avatars.avatar(character), readOnly=True)
        emotionNode = EyeToggleNode('Emotion', IconRegistry.from_name('mdi.emoticon-neutral'))
        motivationNode = EyeToggleNode('Motivation', IconRegistry.from_name('fa5s.fist-raised'))
        conflictNode = EyeToggleNode('Conflict', IconRegistry.conflict_icon())

        emotionNode.toggled.connect(partial(self.characterEmotionToggled.emit, character))
        motivationNode.toggled.connect(partial(self.characterMotivationToggled.emit, character))
        conflictNode.toggled.connect(partial(self.characterConflictToggled.emit, character))
        agendaNode.addChild(emotionNode)
        agendaNode.addChild(motivationNode)
        agendaNode.addChild(conflictNode)

        self._agendaCharactersNode.addChild(agendaNode)


class ArcReport(AbstractReport, Ui_PlotReport):

    def __init__(self, novel: Novel, parent=None):
        super(ArcReport, self).__init__(novel, parent)

        self.chartValues = StoryArcChart(self.novel)
        self.chartViewPlotValues.setChart(self.chartValues)
        self._treeView = ArcsTreeView(novel)
        self._treeView.storylineToggled.connect(self.chartValues.setStorylineVisible)
        self._treeView.conflictToggled.connect(self.chartValues.setConflictVisible)
        self._treeView.characterEmotionToggled.connect(self.chartValues.setCharacterEmotionVisible)
        self._treeView.characterMotivationToggled.connect(self.chartValues.setCharacterMotivationVisible)
        self._treeView.characterConflictToggled.connect(self.chartValues.setCharacterConflictVisible)
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

    # def _plotToggled(self, plot: Plot, toggled: bool):
    #     self.chartValues.setStorylineVisible(plot, toggled)

    # def _conflictToggled(self, toggled: bool):
    #     self.chartValues.setConflictVisible(toggled)


@dataclass
class CharacterArcs:
    emotion: Optional[QAbstractSeries] = None
    conflict: Optional[QAbstractSeries] = None
    motivation: List[QAbstractSeries] = field(default_factory=list)


class StoryArcChart(BaseChart):
    MIN: int = -10
    MAX: int = 10

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self.novel = novel
        self.createDefaultAxes()
        self.legend().setMarkerShape(QLegend.MarkerShape.MarkerShapeCircle)
        self.legend().show()

        self._axisX = QValueAxis()
        self._axisX.setRange(0, len(self.novel.scenes))
        self.addAxis(self._axisX, Qt.AlignmentFlag.AlignBottom)
        self._axisX.setVisible(False)

        self._axisY = QValueAxis()
        self.addAxis(self._axisY, Qt.AlignmentFlag.AlignLeft)
        self._axisY.setRange(self.MIN - 1, self.MAX + 1)
        self._axisY.setVisible(False)

        self._overallConflict: bool = False
        self._overallConflictSeries: Optional[QAbstractSeries] = None
        self._plots: Dict[Plot, List[QAbstractSeries]] = {}

        self._characters: Dict[Character, CharacterArcs] = {}

        self.setTitle('Story arc')

    def setStorylineVisible(self, plot: Plot, visible: bool):
        if visible:
            series = self._storylineSeries(plot)
            for serie in series:
                self.addSeries(serie)
                serie.attachAxis(self._axisY)
            self._plots[plot] = series
        else:
            for serie in self._plots.pop(plot):
                self.removeSeries(serie)

    def setConflictVisible(self, visible: bool):
        if visible:
            self._overallConflictSeries = self._conflictSeries()
            self.addSeries(self._overallConflictSeries)
            self._overallConflictSeries.attachAxis(self._axisY)
        else:
            self.removeSeries(self._overallConflictSeries)
            self._overallConflictSeries = None

        self._overallConflict = visible

    def setCharacterEmotionVisible(self, character: Character, visible: bool):
        arcs = self._characterArcs(character)
        if visible:
            pass
        else:
            self.removeSeries(arcs.emotion)
            arcs.emotion = None

    def setCharacterMotivationVisible(self, character: Character, visible: bool):
        arcs = self._characterArcs(character)
        if visible:
            pass
        else:
            for serie in arcs.motivation:
                self.removeSeries(serie)
            arcs.motivation.clear()

    def setCharacterConflictVisible(self, character: Character, visible: bool):
        arcs = self._characterArcs(character)
        if visible:
            arcs.conflict = self._conflictSeries(character)
            self.addSeries(arcs.conflict)
            arcs.conflict.attachAxis(self._axisY)
        else:
            self.removeSeries(arcs.conflict)
            arcs.conflict = None

    def refresh(self):
        self.reset()
        self._axisX.setRange(0, len(self.novel.scenes))

    def _characterArcs(self, character: Character) -> CharacterArcs:
        if character not in self._characters.keys():
            self._characters[character] = CharacterArcs()

        return self._characters[character]

    def _storylineSeries(self, storyline: Plot) -> List[QAbstractSeries]:
        all_series = []

        for value in storyline.values:
            charge = 0
            series = QSplineSeries()
            all_series.append(series)
            series.setName(icon_to_html_img(IconRegistry.from_name(value.icon, value.icon_color)) + value.text)
            pen = QPen()
            pen.setColor(QColor(value.icon_color))
            pen.setWidth(2)
            series.setPen(pen)
            series.append(0, charge)

            for i, scene in enumerate(self.novel.scenes):
                for scene_ref in scene.plot_values:
                    if scene_ref.plot.id != storyline.id:
                        continue
                    for scene_p_value in scene_ref.data.values:
                        if scene_p_value.plot_value_id == value.id:
                            charge += scene_p_value.charge
                            series.append(i + 1, clamp(charge, self.MIN, self.MAX))

        return all_series

    def _conflictSeries(self, character: Optional[Character] = None) -> QAbstractSeries:
        series = QLineSeries()
        if character:
            avatar = icon_to_html_img(avatars.avatar(character))
        else:
            avatar = ''
        series.setName(avatar + icon_to_html_img(IconRegistry.conflict_icon()) + 'Conflict intensity')
        pen = QPen()
        pen.setColor(QColor('#f3a712'))
        pen.setWidth(2)
        series.setPen(pen)

        for i, scene in enumerate(self.novel.scenes):
            if character and scene.agendas[0].character_id != character.id:
                continue
            intensity = max([x.intensity for x in scene.agendas[0].conflict_references], default=0)
            if intensity > 0:
                series.append(i + 1, intensity)

        return series
