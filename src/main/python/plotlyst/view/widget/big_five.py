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
from functools import partial
from typing import Optional, List, Dict

import qtanim
from PyQt6.QtCharts import QCategoryAxis, QPolarChart, QValueAxis, QAreaSeries, QLineSeries
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import QWidget, QLabel, QDial, QScrollArea, QGridLayout, QProgressBar
from qthandy import vbox, bold, pointy, hbox, grid, decr_font, italic

from src.main.python.plotlyst.core.domain import Character, BigFiveDimension, BigFiveFacet, agreeableness, \
    conscientiousness, neuroticism, extroversion, openness
from src.main.python.plotlyst.core.text import html
from src.main.python.plotlyst.view.widget.chart import PolarBaseChart
from src.main.python.plotlyst.view.widget.display import ChartView


class BigFiveChart(PolarBaseChart):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(html('Big Five Personality Traits').bold())

        self._series: Dict[BigFiveDimension, QAreaSeries] = {}
        self._angles: Dict[BigFiveDimension, List[int]] = {
            openness: [0, 12, 24, 36, 48, 60, 72],
            extroversion: [72, 84, 96, 108, 120, 132, 144],
            neuroticism: [144, 156, 168, 180, 192, 204, 216],
            conscientiousness: [216, 228, 240, 252, 264, 276, 288],
            agreeableness: [288, 300, 312, 324, 336, 348, 360]
        }

        self._rad_axis = QValueAxis()
        self._rad_axis.setRange(0, 100)
        self._rad_axis.setLabelsVisible(False)
        self.addAxis(self._rad_axis, QPolarChart.PolarOrientation.PolarOrientationRadial)
        self._angular_axis = QCategoryAxis()
        self._angular_axis.setRange(0, 360)
        self.addAxis(self._angular_axis, QPolarChart.PolarOrientation.PolarOrientationAngular)

    def refreshDimension(self, dimension: BigFiveDimension, values: List[int]):
        if dimension in self._series.keys():
            self.removeSeries(self._series[dimension])

        upper_series = QLineSeries()
        lower_series = QLineSeries()
        for i, value in enumerate(values):
            upper_series.append(self._angles[dimension][i], value)
            upper_series.append(self._angles[dimension][i + 1], value)
            lower_series.append(self._angles[dimension][i], 1)
            lower_series.append(self._angles[dimension][i + 1], 1)
        lower_series.attachAxis(self._rad_axis)

        area_series = QAreaSeries(upper_series, lower_series)

        pen = QPen()
        pen.setColor(QColor(dimension.color))
        pen.setWidth(2)
        upper_series.setPen(pen)
        lower_series.setPen(pen)
        area_series.setColor(QColor(dimension.color))
        area_series.setOpacity(0.7)
        self._series[dimension] = area_series

        self.addSeries(area_series)
        self.addSeries(upper_series)
        self.addSeries(lower_series)
        area_series.attachAxis(self._angular_axis)
        area_series.attachAxis(self._rad_axis)


class FacetDial(QDial):
    def __init__(self, parent=None):
        super().__init__(parent)
        pointy(self)
        self.setFixedSize(30, 30)
        self.setMinimum(1)
        self.setMaximum(100)
        self.setValue(50)


class BigFiveFacetWidget(QWidget):

    def __init__(self, facet: BigFiveFacet, parent=None):
        super().__init__(parent)
        self._facet = facet

        hbox(self, 0, 0)
        self._lblName = QLabel(self._facet.name.capitalize(), self)
        self._lblName.setWordWrap(True)
        self.dial = FacetDial(self)

        self.layout().addWidget(self.dial, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._lblName, alignment=Qt.AlignmentFlag.AlignCenter)


class BigFiveFacetBarDisplay(QProgressBar):
    def __init__(self, facetWdg: BigFiveFacetWidget, parent=None):
        super().__init__(parent)
        self._facetWdg = facetWdg
        self.setMinimum(1)
        self.setMaximum(100)
        self.setValue(50)

        self._facetWdg.dial.valueChanged.connect(self.setValue)


class BigFivePersonalityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._scrollArea = QScrollArea(self)
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._centralWidget = QWidget()
        self._scrollArea.setWidget(self._centralWidget)
        vbox(self)
        self._gridLayout: QGridLayout = grid(self._centralWidget)
        self._character: Optional[Character] = None

        self._chart = BigFiveChart()
        self._chartView = ChartView(self)
        self._chartView.setChart(self._chart)
        self.layout().addWidget(self._chartView)
        self.layout().addWidget(self._scrollArea)

        self._dimensions: List[BigFiveDimension] = [agreeableness, conscientiousness, neuroticism, extroversion,
                                                    openness]

        self._headers: List[QLabel] = []

        for i, header in enumerate(['Not at all', 'No', 'Not sure', 'Yes', 'Absolutely']):
            lblHeader = QLabel(header, self._centralWidget)
            self._headers.append(lblHeader)
            decr_font(lblHeader)
            italic(lblHeader)
            self._gridLayout.addWidget(lblHeader, 0, 1 + i, alignment=Qt.AlignmentFlag.AlignCenter)

        for i, dim_ in enumerate(self._dimensions):
            _lblDimName = QLabel(dim_.name.capitalize(), self._centralWidget)
            bold(_lblDimName)
            self._gridLayout.addWidget(_lblDimName, 1 + i * 7, 0)
            for j, facet in enumerate(dim_.facets):
                facet = BigFiveFacetWidget(facet, self._centralWidget)
                self._gridLayout.addWidget(facet, i * 7 + j + 2, 0, alignment=Qt.AlignmentFlag.AlignLeft)
                display = BigFiveFacetBarDisplay(facet, self._centralWidget)
                self._gridLayout.addWidget(display, i * 7 + j + 2, 1, 1, 5)

                facet.dial.valueChanged.connect(partial(self._facetEdited, facet, dim_))

    def setCharacter(self, character: Character):
        self._character = character

        for bf, values in self._character.big_five.items():
            self._chart.refreshDimension(self._dimension(bf), values)

    def _dimension(self, name: str):
        if name == agreeableness.name:
            return agreeableness
        elif name == openness.name:
            return openness
        elif name == extroversion.name:
            return extroversion
        elif name == neuroticism.name:
            return neuroticism
        else:
            return conscientiousness

    def _facetEdited(self, facet: BigFiveFacetWidget, dimension: BigFiveDimension, value: int):
        if value <= 20:
            qtanim.glow(self._headers[0], duration=50)
        elif value <= 40:
            qtanim.glow(self._headers[1], duration=50)
        elif value <= 60:
            qtanim.glow(self._headers[2], duration=50)
        elif value <= 80:
            qtanim.glow(self._headers[3], duration=50)
        else:
            qtanim.glow(self._headers[4], duration=50)

        if not facet.dial.isSliderDown():
            self._chart.refreshDimension(dimension, [1, 3, 4, 1, 2, 3])
