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
from typing import Optional, List

import qtanim
from PyQt6.QtCharts import QCategoryAxis, QPolarChart, QSplineSeries
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtWidgets import QWidget, QLabel, QDial, QScrollArea, QGridLayout, QProgressBar
from qthandy import vbox, bold, pointy, hbox, grid, decr_font, italic

from src.main.python.plotlyst.core.domain import Character, BigFiveDimension, BigFiveFacet, agreeableness, \
    conscientiousness, neuroticism, extroversion, openness
from src.main.python.plotlyst.core.text import html
from src.main.python.plotlyst.view.common import icon_to_html_img
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.chart import PolarBaseChart
from src.main.python.plotlyst.view.widget.display import ChartView


class BigFiveChart(PolarBaseChart):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(html('Big Five Personality Traits').bold())

    def refresh(self):
        self.reset()

        axis = QCategoryAxis()
        axis.setRange(0, 360)
        img = icon_to_html_img(IconRegistry.book_icon())
        axis.append(img, 90)

        series = QSplineSeries()
        pen = QPen()
        pen.setColor(QColor('#f3a712'))
        pen.setWidth(2)
        series.setPen(pen)

        series.append(1, 1)
        series.append(80, 3)
        series.append(160, 5)
        series.append(240, 5)
        series.append(300, 3)

        self.addAxis(axis, QPolarChart.PolarOrientation.PolarOrientationAngular)

        self.addSeries(series)
        series.attachAxis(axis)


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

                facet.dial.valueChanged.connect(partial(self._facetEdited, facet))

    def setCharacter(self, character: Character):
        self._character = character

    def _facetEdited(self, facet: BigFiveFacetWidget, value: int):
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
            self._chart.refresh()
