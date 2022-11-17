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
from typing import Optional, List

from PyQt6.QtWidgets import QWidget, QLabel, QDial
from qthandy import vbox, hbox

from src.main.python.plotlyst.core.domain import Character, BigFiveDimension, BigFiveFacet, agreeableness, \
    conscientiousness, neuroticism, extroversion, openness
from src.main.python.plotlyst.view.widget.chart import BaseChart
from src.main.python.plotlyst.view.widget.display import ChartView


class BigFiveChart(BaseChart):
    def __init__(self, parent=None):
        super().__init__(parent)


class BigFiveFacetWidget(QWidget):
    def __init__(self, facet: BigFiveFacet, parent=None):
        super().__init__(parent)
        self._facet = facet

        vbox(self)
        self._lblName = QLabel(self._facet.name, self)
        self._dial = QDial(self)

        self.layout().addWidget(self._dial)
        self.layout().addWidget(self._lblName)


class BigFiveDimensionWidget(QWidget):
    def __init__(self, dimension: BigFiveDimension, parent=None):
        super().__init__(parent)
        self._dimension = dimension

        self._facets: List[BigFiveFacetWidget] = []
        self._lblName = QLabel(self._dimension.name, self)

        vbox(self).addWidget(self._lblName)
        self._facetsContainer = QWidget(self)
        hbox(self._facetsContainer)
        self.layout().addWidget(self._facetsContainer)

        for facet in self._dimension.facets:
            wdg = BigFiveFacetWidget(facet, self)
            self._facets.append(wdg)
            self._facetsContainer.layout().addWidget(wdg)


class BigFivePersonalityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        vbox(self)
        self._character: Optional[Character] = None

        self._chart = BigFiveChart()
        self._chartView = ChartView(self)
        self._chartView.setChart(self._chart)
        self.layout().addWidget(self._chartView)

        self._dimensions: List[BigFiveDimension] = [agreeableness, conscientiousness, neuroticism, extroversion,
                                                    openness]
        for dim_ in self._dimensions:
            wdg = BigFiveDimensionWidget(dim_)
            self.layout().addWidget(wdg)

    def setCharacter(self, character: Character):
        self._character = character
