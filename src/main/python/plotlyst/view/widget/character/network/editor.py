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
from typing import Optional

from PyQt6.QtWidgets import QButtonGroup
from qthandy import vline

from src.main.python.plotlyst.view.common import tool_btn
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.graphics import BaseItemEditor, SolidPenStyleSelector, DashPenStyleSelector, \
    DotPenStyleSelector, ConnectorItem


class ConnectorEditor(BaseItemEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._connector: Optional[ConnectorItem] = None

        self._btnColor = tool_btn(IconRegistry.from_name('fa5s.circle', color='darkBlue'), 'Change style',
                                  transparent_=True)

        self._solidLine = SolidPenStyleSelector()
        self._dashLine = DashPenStyleSelector()
        self._dotLine = DotPenStyleSelector()
        self._lineBtnGroup = QButtonGroup()
        self._lineBtnGroup.addButton(self._solidLine)
        self._lineBtnGroup.addButton(self._dashLine)
        self._lineBtnGroup.addButton(self._dotLine)
        self._lineBtnGroup.buttonClicked.connect(self._penStyleChanged)

        self._toolbar.layout().addWidget(self._btnColor)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._solidLine)
        self._toolbar.layout().addWidget(self._dashLine)
        self._toolbar.layout().addWidget(self._dotLine)

    def setItem(self, connector: ConnectorItem):
        self._connector = connector

    def _penStyleChanged(self):
        btn = self._lineBtnGroup.checkedButton()
        if btn:
            self._connector.setPenStyle(btn.penStyle())
