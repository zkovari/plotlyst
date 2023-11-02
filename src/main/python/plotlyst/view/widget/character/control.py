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

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QSpinBox, QSlider, QTextBrowser
from overrides import overrides
from qthandy import vbox, pointy, hbox, line, sp
from qtmenu import MenuWidget

from src.main.python.plotlyst.view.common import spawn, push_btn


@spawn
class CharacterAgeEditor(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._wdgEditor = QWidget()
        self._wdgHintDisplay = QWidget()
        hbox(self)
        self.layout().addWidget(self._wdgEditor)
        self.layout().addWidget(line())
        self.layout().addWidget(self._wdgHintDisplay)

        self._slider = QSlider(self)
        self._slider.setMinimum(1)
        self._slider.setMaximum(100)
        self._slider.setValue(1)
        sp(self._slider).v_exp()
        pointy(self._slider)

        self._spinbox = QSpinBox(self)
        self._spinbox.setPrefix('Age: ')
        self._spinbox.setMinimum(0)
        self._spinbox.setMaximum(65000)
        self._spinbox.setValue(0)

        self._btnStage = push_btn(transparent_=True)
        self._menuStages = MenuWidget(self._btnStage)
        self._menuStages.addSection('Select a stage')
        self._menuStages.addSeparator()

        self._text = QTextBrowser()

        vbox(self._wdgHintDisplay)
        self._wdgHintDisplay.layout().addWidget(self._btnStage, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgHintDisplay.layout().addWidget(self._text)

        # self._iconBaby = Icon(self)
        # self._iconBaby.setIcon(IconRegistry.baby_icon())
        # self._iconBaby.setToolTip('Baby')
        # self._iconAdult = Icon(self)
        # self._iconAdult.setIcon(IconRegistry.adult_icon())
        # self._iconAdult.setToolTip('Adult')
        # self._iconOld = Icon(self)
        # self._iconOld.setIcon(IconRegistry.elderly_icon())
        # self._iconOld.setToolTip('Elderly')

        # self.layout().addWidget(vspacer(20))
        # self.layout().addWidget(
        #     group(wrap(self._iconAdult, margin_bottom=25), self._slider, wrap(self._iconOld, margin_bottom=20),
        #           spacing=1),
        #     alignment=Qt.AlignmentFlag.AlignCenter)
        # self.layout().addWidget(self._iconBaby, alignment=Qt.AlignmentFlag.AlignCenter)
        # self.layout().addWidget(line())

        vbox(self._wdgEditor)
        self._wdgEditor.layout().addWidget(self._slider, alignment=Qt.AlignmentFlag.AlignCenter)
        self._wdgEditor.layout().addWidget(self._spinbox)

        self._slider.valueChanged.connect(self._sliderValueChanged)
        self._spinbox.valueChanged.connect(self._spinboxValueChanged)

    def value(self) -> int:
        return self._spinbox.value()

    def setValue(self, age: int):
        self._spinbox.setValue(age)

    @overrides
    def setFocus(self):
        self._spinbox.setFocus()

    def minimum(self) -> int:
        return self._spinbox.minimum()

    def _sliderValueChanged(self, value: int):
        if value != self._spinbox.value():
            if value == self._slider.maximum() and self._spinbox.value() >= value:
                return

            self._spinbox.setValue(value)

    def _spinboxValueChanged(self, value: int):
        self._spinbox.setMinimum(1)
        if value != self._slider.value():
            if value > self._slider.maximum():
                self._slider.setValue(self._slider.maximum())
            else:
                self._slider.setValue(value)

        self.valueChanged.emit(value)
