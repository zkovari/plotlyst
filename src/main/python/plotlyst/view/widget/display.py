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

from PyQt5.QtChart import QChartView
from PyQt5.QtCore import QPropertyAnimation
from PyQt5.QtGui import QPainter, QShowEvent
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QToolButton, QSizePolicy
from overrides import overrides

from src.main.python.plotlyst.view.common import bold, increase_font, transparent, spacer_widget
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.layout import vbox, group


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


class Chart(QChartView):
    def __init__(self, parent=None):
        super(Chart, self).__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)


class Subtitle(QWidget):
    def __init__(self, parent=None):
        super(Subtitle, self).__init__(parent)
        vbox(self, margin=0, spacing=0)
        self.lblTitle = QLabel(self)
        self.icon = QToolButton(self)
        transparent(self.icon)
        self.lblDescription = QLabel(self)
        bold(self.lblTitle)
        increase_font(self.lblTitle)

        self._iconName: str = ''
        self._descSpacer = spacer_widget(20)

        self.lblDescription.setStyleSheet('color: #8d99ae;')
        self.lblDescription.setWordWrap(True)
        self.lblDescription.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.layout().addWidget(group(self.icon, self.lblTitle, parent=self))
        self.layout().addWidget(group(self._descSpacer, self.lblDescription, parent=self))

    def setIconName(self, icon: str):
        self._iconName = icon

    @overrides
    def showEvent(self, event: QShowEvent) -> None:
        if not self.lblTitle.text():
            self.lblTitle.setText(self.property('title'))
        if not self.lblDescription.text():
            desc = self.property('description')
            if desc:
                self.lblDescription.setText(desc)
            else:
                self.lblDescription.setHidden(True)
        if not self._iconName:
            self._iconName = self.property('icon')

        if self._iconName:
            self.icon.setIcon(IconRegistry.from_name(self._iconName))
            self._descSpacer.setMaximumWidth(20)
        else:
            self.icon.setHidden(True)
            self._descSpacer.setMaximumWidth(5)
