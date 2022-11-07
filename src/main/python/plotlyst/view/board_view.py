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

from overrides import overrides
from qthandy import vbox

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.widget.task import BoardWidget


class BoardView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        vbox(self.widget)

        self._board = BoardWidget(novel)
        self.widget.layout().addWidget(self._board)

    @overrides
    def refresh(self):
        pass
