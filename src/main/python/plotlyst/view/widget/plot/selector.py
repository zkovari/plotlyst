"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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

from functools import partial
from typing import Dict

from PyQt6.QtCore import pyqtSignal
from qtmenu import MenuWidget

from plotlyst.core.domain import Novel, Plot, PlotType
from plotlyst.view.common import action
from plotlyst.view.icons import IconRegistry


class StorylineSelectorMenu(MenuWidget):
    storylineSelected = pyqtSignal(Plot)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._filters: Dict[PlotType, bool] = {
            PlotType.Global: True,
            PlotType.Main: True,
            PlotType.Internal: True,
            PlotType.Subplot: True,
            PlotType.Relation: True,
        }
        self.aboutToShow.connect(self._beforeShow)

    def filterPlotType(self, plotType: PlotType, filtered: bool):
        self._filters[plotType] = filtered

    def filterAll(self, filtered: bool):
        for k in self._filters.keys():
            self._filters[k] = filtered

    def _beforeShow(self):
        self.clear()
        for plot in self._novel.plots:
            if not self._filters[plot.plot_type]:
                continue
            action_ = action(plot.text, IconRegistry.from_name(plot.icon, plot.icon_color),
                             partial(self.storylineSelected.emit, plot))
            self.addAction(action_)
        if not self.actions():
            self.addSection('No corresponding storylines were found')
