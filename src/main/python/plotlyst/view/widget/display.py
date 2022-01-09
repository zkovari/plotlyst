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
from typing import Optional

from PyQt5.QtCore import QPropertyAnimation
from PyQt5.QtWidgets import QPushButton, QWidget

from src.main.python.plotlyst.view.icons import IconRegistry


class ToggleHelp(QPushButton):
    def __init__(self, parent=None):
        super(ToggleHelp, self).__init__(parent)
        self.setStyleSheet('border: 0px;')
        self.setIcon(IconRegistry.general_info_icon())
        self.setText(u'\u00BB')

        self._attachedWidget: Optional[QWidget] = None
        self.clicked.connect(self._clicked)

    def attachWidget(self, widget: QWidget):
        self.setCheckable(True)
        self._attachedWidget = widget
        self._attachedWidget.setVisible(False)

    def _clicked(self, checked: bool):
        if self._attachedWidget is None:
            return

        if checked:
            self._attachedWidget.setVisible(checked)
            animation = QPropertyAnimation(self._attachedWidget, b'maximumHeight', self)
            animation.setStartValue(10)
            animation.setEndValue(200)
            animation.start()
        else:
            animation = QPropertyAnimation(self._attachedWidget, b'maximumHeight', self)
            animation.setStartValue(200)
            animation.setEndValue(0)
            animation.start()

        self.setText(u'\u02C7' if checked else u'\u00BB')
