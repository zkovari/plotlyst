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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QWidget
from overrides import overrides
from qthandy import vbox

from src.main.python.plotlyst.core.domain import Novel, WorldBuildingEntity
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.widget.world_building import WorldBuildingEditor


class WorldBuildingView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)

        self.widget = QWidget()
        self.widget.setPalette(QPalette(Qt.GlobalColor.white))
        vbox(self.widget, 10)

        self._editor = WorldBuildingEditor(WorldBuildingEntity('My new world'))
        self.widget.layout().addWidget(self._editor)

    @overrides
    def refresh(self):
        pass
