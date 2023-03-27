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
from overrides import overrides
from qthandy import bold
from qthandy.filter import InstantTooltipEventFilter

from src.main.python.plotlyst.common import PLOTLYST_SECONDARY_COLOR
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view._view import AbstractNovelView
from src.main.python.plotlyst.view.common import scroll_to_bottom
from src.main.python.plotlyst.view.generated.board_view_ui import Ui_BoardView
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.task import BoardWidget


class BoardView(AbstractNovelView):

    def __init__(self, novel: Novel):
        super().__init__(novel)
        self.ui = Ui_BoardView()
        self.ui.setupUi(self.widget)
        self.widget.setObjectName('boardParentWidget')
        self.widget.setStyleSheet('#boardParentWidget {background: #f3f3f6;}')

        self.ui.btnNew.setIcon(IconRegistry.plus_icon('white'))
        self.ui.btnBoard.setIcon(IconRegistry.from_name('fa5s.columns', color_on=PLOTLYST_SECONDARY_COLOR))
        self.ui.btnChart.setIcon(IconRegistry.from_name('mdi.chart-areaspline', color_on=PLOTLYST_SECONDARY_COLOR))
        self.ui.btnSettings.setIcon(IconRegistry.cog_icon())
        self.ui.btnChart.installEventFilter(InstantTooltipEventFilter(self.ui.btnChart))
        self.ui.btnSettings.installEventFilter(InstantTooltipEventFilter(self.ui.btnSettings))

        bold(self.ui.lblTitle)
        self.ui.iconBoard.setIcon(IconRegistry.board_icon())

        self._board = BoardWidget(novel)
        self.ui.scrollAreaWidgetContents.layout().addWidget(self._board)
        self._board.taskAdded.connect(lambda: scroll_to_bottom(self.ui.scrollArea))

        self.ui.btnNew.clicked.connect(self._board.addNewTask)

        self.ui.btnBoard.setChecked(True)

    @overrides
    def refresh(self):
        pass
