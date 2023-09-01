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

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QButtonGroup
from qthandy import vline

from src.main.python.plotlyst.core.domain import RelationsNetwork, Relation
from src.main.python.plotlyst.view.common import tool_btn
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.graphics import BaseItemEditor, SolidPenStyleSelector, DashPenStyleSelector, \
    DotPenStyleSelector, ConnectorItem, PenWidthEditor, RelationsButton, SecondarySelectorWidget


class RelationSelector(SecondarySelectorWidget):
    relationSelected = pyqtSignal(Relation)

    def __init__(self, network: RelationsNetwork, parent=None):
        super().__init__(parent)
        self._network = network
        self._romance = Relation('Romance', icon='ei.heart', icon_color='#d1495b')
        self._friendship = Relation('Friendship', icon='fa5s.user-friends', icon_color='#457b9d')
        self._sidekick = Relation('Sidekick', icon='ei.asl', icon_color='#b0a990')
        self._guide = Relation('Guide', icon='mdi.compass-rose', icon_color='#80ced7')
        self._newRelationButton(self._romance, 0, 0)
        self._newRelationButton(self._friendship, 0, 1)
        self._newRelationButton(self._sidekick, 0, 2)
        self._newRelationButton(self._guide, 1, 0)

    def _newRelationButton(self, relation: Relation, row: int, col: int):
        btn = self._newButton(IconRegistry.from_name(relation.icon), relation.text, row, col)
        btn.clicked.connect(lambda: self.relationSelected.emit(relation))


class ConnectorEditor(BaseItemEditor):
    def __init__(self, network: RelationsNetwork, parent=None):
        super().__init__(parent)
        self._connector: Optional[ConnectorItem] = None

        self._btnRelationType = RelationsButton()

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

        self._sbWidth = PenWidthEditor()
        self._sbWidth.valueChanged.connect(self._widthChanged)

        self._relationSelector = RelationSelector(network, self)
        self._relationSelector.relationSelected.connect(self._relationChanged)
        self.addSecondaryWidget(self._btnRelationType, self._relationSelector)

        self._toolbar.layout().addWidget(self._btnRelationType)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._btnColor)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._solidLine)
        self._toolbar.layout().addWidget(self._dashLine)
        self._toolbar.layout().addWidget(self._dotLine)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._sbWidth)

    def setItem(self, connector: ConnectorItem):
        self._connector = connector

    def _relationChanged(self, relation: Relation):
        self._connector.setRelation(relation)

    def _penStyleChanged(self):
        btn = self._lineBtnGroup.checkedButton()
        if btn:
            self._connector.setPenStyle(btn.penStyle())

    def _widthChanged(self, value: int):
        self._connector.setPenWidth(value)
