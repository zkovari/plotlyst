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
from PyQt6.QtCharts import QCategoryAxis, QPolarChart, QValueAxis, QAreaSeries, QSplineSeries
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPen, QWheelEvent
from PyQt6.QtWidgets import QWidget, QLabel, QScrollArea, QGridLayout, QSlider
from overrides import overrides
from qthandy import vbox, bold, pointy, hbox, grid, decr_font, italic

from src.main.python.plotlyst.core.domain import Character, BigFiveDimension, BigFiveFacet, agreeableness, \
    conscientiousness, neuroticism, extroversion, openness
from src.main.python.plotlyst.core.text import html
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.chart import PolarBaseChart
from src.main.python.plotlyst.view.widget.display import ChartView, IconText


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
            area_series = self._series[dimension]
            self.removeSeries(area_series.upperSeries())
            self.removeSeries(area_series.lowerSeries())
            self.removeSeries(area_series)

        upper_series = QSplineSeries()
        lower_series = QSplineSeries()
        for i, value in enumerate(values):
            upper_series.append(self._angles[dimension][i], value)
            upper_series.append(self._angles[dimension][i + 1], value)
            lower_series.append(self._angles[dimension][i], 1)
            lower_series.append(self._angles[dimension][i + 1], 1)

        self.addSeries(upper_series)
        self.addSeries(lower_series)
        area_series = QAreaSeries(upper_series, lower_series)

        pen = QPen()
        pen.setColor(QColor(dimension.color))
        pen.setWidth(3)
        upper_series.setPen(pen)
        lower_series.setPen(pen)
        area_series.setPen(pen)
        area_series.setColor(QColor(dimension.color))
        area_series.setOpacity(0.7)
        self._series[dimension] = area_series

        self.addSeries(area_series)
        area_series.attachAxis(self._angular_axis)
        area_series.attachAxis(self._rad_axis)


class BigFiveValueLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._animated: bool = False

    def animate(self):
        if self._animated:
            return
        self._animated = True
        anim = qtanim.glow(self)
        anim.finished.connect(self._finished)

    def _finished(self):
        self._animated = False


class FacetSlider(QSlider):
    def __init__(self, dimension: BigFiveDimension, parent=None):
        super().__init__(parent)
        self._dimension = dimension
        self.setOrientation(Qt.Orientation.Horizontal)
        pointy(self)
        self.setMinimum(1)
        self.setMaximum(100)
        self.setValue(50)
        self.setTracking(False)
        self.setStyleSheet(f'''
            QSlider::add-page:horizontal {{
                background: lightgray;
            }}
            QSlider::sub-page:horizontal {{
                background: {self._dimension.color};
            }}
        ''')

    @overrides
    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()


class BigFiveFacetWidget(QWidget):

    def __init__(self, facet: BigFiveFacet, parent=None):
        super().__init__(parent)
        self._facet = facet

        hbox(self, 0, 0)
        self._lblName = QLabel(self._facet.name.capitalize(), self)
        self._lblName.setWordWrap(True)
        self.layout().addWidget(self._lblName, alignment=Qt.AlignmentFlag.AlignCenter)


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

        self._headers: List[BigFiveValueLabel] = []

        for i, header in enumerate(['Not at all', 'No', 'Not sure', 'Yes', 'Absolutely']):
            lblHeader = BigFiveValueLabel(header, self._centralWidget)
            self._headers.append(lblHeader)
            decr_font(lblHeader)
            italic(lblHeader)
            self._gridLayout.addWidget(lblHeader, 0, 1 + i, alignment=Qt.AlignmentFlag.AlignCenter)

        self._facetWidgets: Dict[BigFiveDimension, List[FacetSlider]] = {}
        for i, dim_ in enumerate(self._dimensions):
            _lblDimName = IconText(self._centralWidget)
            _lblDimName.setText(dim_.name.capitalize())
            _lblDimName.setIcon(IconRegistry.from_name(dim_.icon, dim_.color))
            bold(_lblDimName)
            self._gridLayout.addWidget(_lblDimName, 1 + i * 7, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            self._facetWidgets[dim_] = []
            for j, facet in enumerate(dim_.facets):
                facet = BigFiveFacetWidget(facet, self._centralWidget)
                self._gridLayout.addWidget(facet, i * 7 + j + 2, 0, alignment=Qt.AlignmentFlag.AlignRight)
                slider = FacetSlider(dim_, self._centralWidget)
                self._facetWidgets[dim_].append(slider)
                self._gridLayout.addWidget(slider, i * 7 + j + 2, 1, 1, 5)

                slider.sliderMoved.connect(self._facetEdited)
                slider.valueChanged.connect(partial(self._facetChanged, dim_))

    def setCharacter(self, character: Character):
        self._character = None

        for bf, values in character.big_five.items():
            for i, v in enumerate(values):
                self._facetWidgets[self._dimension(bf)][i].setValue(v)
        for bf, values in character.big_five.items():
            self._chart.refreshDimension(self._dimension(bf), values)

        self._character = character

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

    def _facetEdited(self, value: int):
        if value <= 20:
            header = self._headers[0]
        elif value <= 40:
            header = self._headers[1]
        elif value <= 60:
            header = self._headers[2]
        elif value <= 80:
            header = self._headers[3]
        else:
            header = self._headers[4]
        header.animate()

    def _facetChanged(self, dimension: BigFiveDimension):
        if self._character is None:
            return
        self._character.big_five[dimension.name] = [x.value() for x in self._facetWidgets[dimension]]
        self._chart.refreshDimension(dimension, self._character.big_five[dimension.name])
