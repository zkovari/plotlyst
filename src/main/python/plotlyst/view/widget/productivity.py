"""
Plotlyst
Copyright (C) 2021-2025  Zsolt Kovari

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
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget
from overrides import overrides
from qthandy import vbox, hbox, pointy
from qthandy.filter import OpacityEventFilter
from qtmenu import MenuWidget

from plotlyst.common import PLOTLYST_SECONDARY_COLOR
from plotlyst.env import app_env
from plotlyst.view.common import label
from plotlyst.view.icons import IconRegistry
from plotlyst.view.style.button import apply_button_palette_color
from plotlyst.view.widget.display import IconText


class ProductivityTrackingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        vbox(self)
        self.layout().addWidget(label('Test that is longer thatn asdsfsidjfs dfsd'))


class ProductivityButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        hbox(self, spacing=0)

        self.icon = IconText()
        self.icon.setIcon(IconRegistry.from_name('mdi6.progress-star-four-points', color=PLOTLYST_SECONDARY_COLOR))
        self.icon.setText('Days:')
        apply_button_palette_color(self.icon, PLOTLYST_SECONDARY_COLOR)
        self.icon.clicked.connect(self._popup)

        self.streak = label('0', incr_font_diff=4, color=PLOTLYST_SECONDARY_COLOR)
        self.streak.setStyleSheet(f'''
            color: {PLOTLYST_SECONDARY_COLOR};
            font-family: {app_env.serif_font()};
            ''')

        self.trackingWdg = ProductivityTrackingWidget()
        self._menu = MenuWidget()
        self._menu.addWidget(self.trackingWdg)

        self.layout().addWidget(self.icon)
        self.layout().addWidget(self.streak)

        pointy(self)
        self.installEventFilter(OpacityEventFilter(self, leaveOpacity=0.7))

    @overrides
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._popup()

    def _popup(self):
        self._menu.exec(self.mapToGlobal(QPoint(0, self.sizeHint().height() + 10)))
