"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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

from PyQt6.QtWidgets import QWidget
from qthandy import vbox, incr_icon, incr_font
from qthandy.filter import OpacityEventFilter

from plotlyst.core.domain import Scene
from plotlyst.view.common import push_btn
from plotlyst.view.icons import IconRegistry


class SceneFunctionsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene: Optional[Scene] = None

        vbox(self)
        self.btnPrimary = push_btn(IconRegistry.from_name('mdi6.note-text-outline', 'grey'), 'Primary',
                                   transparent_=True)
        incr_icon(self.btnPrimary, 2)
        incr_font(self.btnPrimary, 2)
        self.btnPrimary.installEventFilter(OpacityEventFilter(self.btnPrimary, leaveOpacity=0.7))
        self.btnSecondary = push_btn(IconRegistry.from_name('fa5s.list', 'grey'), 'Secondary',
                                     transparent_=True)
        self.btnSecondary.installEventFilter(OpacityEventFilter(self.btnSecondary, leaveOpacity=0.7))
        incr_icon(self.btnSecondary, 1)
        incr_font(self.btnSecondary, 1)
        self.layout().addWidget(self.btnPrimary)
        self.layout().addWidget(self.btnSecondary)

    def setScene(self, scene: Scene):
        self._scene = scene
