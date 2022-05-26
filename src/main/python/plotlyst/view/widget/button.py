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

import qtanim
from PyQt5.QtCore import pyqtSignal, Qt, pyqtProperty
from PyQt5.QtWidgets import QPushButton, QSizePolicy, QToolButton, QAbstractButton, QLabel, QButtonGroup
from overrides import overrides
from qthandy import hbox, opaque

from src.main.python.plotlyst.core.domain import SelectionItem
from src.main.python.plotlyst.view.common import OpacityEventFilter
from src.main.python.plotlyst.view.icons import IconRegistry


class SelectionItemPushButton(QPushButton):
    itemClicked = pyqtSignal(SelectionItem)

    def __init__(self, parent=None):
        super(SelectionItemPushButton, self).__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def setSelectionItem(self, item: SelectionItem):
        self.setText(item.text)
        if item.icon:
            self.setIcon(IconRegistry.from_name(item.icon, item.icon_color))

        self.clicked.connect(partial(self.itemClicked.emit, item))
        self.toggled.connect(self._toggled)

    def _toggled(self, checked: bool):
        font = self.font()
        font.setBold(checked)
        self.setFont(font)


class _SecondaryActionButton(QAbstractButton):
    def __init__(self, parent=None):
        super(_SecondaryActionButton, self).__init__(parent)
        self._iconName: str = ''
        self._iconColor: str = 'black'
        self.initStyleSheet()
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        self.installEventFilter(OpacityEventFilter(leaveOpacity=0.7, parent=self))

    def initStyleSheet(self, border_color: str = 'grey', border_color_checked: str = 'black'):
        self.setStyleSheet(f'''
                {self.__class__.__name__} {{
                    border: 2px dashed {border_color};
                    border-radius: 6px;
                    color: grey;
                    padding: 2px;
                }}
                {self.__class__.__name__}:pressed {{
                    border: 2px solid {border_color};
                }}
                {self.__class__.__name__}:checked {{
                    border: 2px solid {border_color_checked};
                }}
            ''')

    def setBorderColor(self, color_name: str):
        self.initStyleSheet(color_name)
        self.update()

    def _setIcon(self):
        if self._iconName:
            self.setIcon(IconRegistry.from_name(self._iconName, self._iconColor))


class SecondaryActionToolButton(QToolButton, _SecondaryActionButton):
    @pyqtProperty(str)
    def iconName(self):
        return self._iconName

    @iconName.setter
    def iconName(self, value):
        self._iconName = value
        self._setIcon()

    @pyqtProperty(str)
    def iconColor(self):
        return self._iconColor

    @iconColor.setter
    def iconColor(self, value):
        self._iconColor = value
        self._setIcon()


class SecondaryActionPushButton(QPushButton, _SecondaryActionButton):
    @pyqtProperty(str)
    def iconName(self):
        return self._iconName

    @iconName.setter
    def iconName(self, value):
        self._iconName = value
        self._setIcon()

    @pyqtProperty(str)
    def iconColor(self):
        return self._iconColor

    @iconColor.setter
    def iconColor(self, value):
        self._iconColor = value
        self._setIcon()


class WordWrappedPushButton(QPushButton):
    def __init__(self, parent=None):
        super(WordWrappedPushButton, self).__init__(parent)
        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.NoTextInteraction)
        self.label.setAlignment(Qt.AlignCenter)
        hbox(self, 0, 0).addWidget(self.label, alignment=Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)

    @overrides
    def setText(self, text: str):
        self.label.setText(text)
        self.setFixedHeight(self.label.height() + 5)


class FadeOutButtonGroup(QButtonGroup):
    def __init__(self, parent=None):
        super(FadeOutButtonGroup, self).__init__(parent)
        self.buttonClicked.connect(self._clicked)
        self.setExclusive(False)
        self._opacity = 0.7
        self._fadeInDuration = 250

    def setButtonOpacity(self, opacity: float):
        self._opacity = opacity

    def setFadeInDuration(self, duration: int):
        self._fadeInDuration = duration

    def _clicked(self, btn: QAbstractButton):
        for other_btn in self.buttons():
            if other_btn is btn:
                continue

            if btn.isChecked():
                other_btn.setChecked(False)
                qtanim.fade_out(other_btn)
            else:
                anim = qtanim.fade_in(other_btn, duration=self._fadeInDuration)
                anim.finished.connect(partial(opaque, other_btn, self._opacity))
