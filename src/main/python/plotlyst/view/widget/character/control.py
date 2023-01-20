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
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QDial, QSpinBox
from qthandy import vbox, line, vspacer

from src.main.python.plotlyst.view.common import pointy
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.display import Icon


class CharacterAgeEditor(QWidget):
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
        self.layout().addWidget(self._dial, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self._iconBaby, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(line())
        self.layout().addWidget(self._spinbox)

        self._iconAdult.setGeometry(3, 1, 20, 20)
        self._iconOld.setGeometry(70, 10, 22, 22)

        self._dial.valueChanged.connect(self._spinbox.setValue)

    def setValue(self, age: int):
        self._spinbox.setValue(age)

    def setFocus(self):
        self._spinbox.setFocus()
