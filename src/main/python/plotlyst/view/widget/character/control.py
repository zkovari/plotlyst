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

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QDial, QSpinBox
from qthandy import vbox, line, vspacer, pointy

from src.main.python.plotlyst.view.common import  wrap
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import group
from src.main.python.plotlyst.view.widget.display import Icon


class CharacterAgeEditor(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._dial = QDial(self)
        self._dial.setMinimum(1)
        self._dial.setMaximum(100)
        self._dial.setFixedSize(60, 60)
        self._dial.setValue(1)
        pointy(self._dial)

        self._spinbox = QSpinBox(self)
        self._spinbox.setPrefix('Age: ')
        self._spinbox.setMinimum(0)
        self._spinbox.setMaximum(65000)
        self._spinbox.setValue(0)

        self._iconBaby = Icon(self)
        self._iconBaby.setIcon(IconRegistry.baby_icon())
        self._iconBaby.setToolTip('Baby')
        self._iconAdult = Icon(self)
        self._iconAdult.setIcon(IconRegistry.adult_icon())
        self._iconAdult.setToolTip('Adult')
        self._iconOld = Icon(self)
        self._iconOld.setIcon(IconRegistry.elderly_icon())
        self._iconOld.setToolTip('Elderly')

        vbox(self, spacing=0)
        self.layout().addWidget(vspacer(20))
        self.layout().addWidget(
            group(wrap(self._iconAdult, margin_bottom=25), self._dial, wrap(self._iconOld, margin_bottom=20),
                  spacing=1),
            alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._iconBaby, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(line())
        self.layout().addWidget(self._spinbox)

        self._dial.valueChanged.connect(self._dialValueChanged)
        self._spinbox.valueChanged.connect(self._spinboxValueChanged)

    def value(self) -> int:
        return self._spinbox.value()

    def setValue(self, age: int):
        self._spinbox.setValue(age)

    def setFocus(self):
        self._spinbox.setFocus()

    def minimum(self) -> int:
        return self._spinbox.minimum()

    def _dialValueChanged(self, value: int):
        if value != self._spinbox.value():
            if value == self._dial.maximum() and self._spinbox.value() >= value:
                return

            self._spinbox.setValue(value)

    def _spinboxValueChanged(self, value: int):
        self._spinbox.setMinimum(1)
        if value != self._dial.value():
            if value > self._dial.maximum():
                self._dial.setValue(self._dial.maximum())
            else:
                self._dial.setValue(value)

        self.valueChanged.emit(value)
