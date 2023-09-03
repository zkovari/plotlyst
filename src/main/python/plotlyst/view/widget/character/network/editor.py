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
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import QButtonGroup
from qthandy import vline
from qtmenu import GridMenuWidget

from src.main.python.plotlyst.core.domain import RelationsNetwork, Relation
from src.main.python.plotlyst.view.common import tool_btn, action
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.graphics import BaseItemEditor, SolidPenStyleSelector, DashPenStyleSelector, \
    DotPenStyleSelector, ConnectorItem, PenWidthEditor, RelationsButton, SecondarySelectorWidget
from src.main.python.plotlyst.view.widget.utility import ColorPicker


class RelationSelector(GridMenuWidget):
    relationSelected = pyqtSignal(Relation)

    def __init__(self, network: RelationsNetwork, parent=None):
        super().__init__(parent)
        self._network = network
        self._romance = Relation('Romance', icon='ei.heart', icon_color='#d1495b')
        self._friendship = Relation('Friendship', icon='fa5s.user-friends', icon_color='#457b9d')
        self._sidekick = Relation('Sidekick', icon='ei.asl', icon_color='#b0a990')
        self._guide = Relation('Guide', icon='mdi.compass-rose', icon_color='#80ced7')

        self._newAction(self._romance, 0, 0)
        self._newAction(self._friendship, 0, 1)
        self._newAction(self._sidekick, 0, 2)
        self._newAction(self._guide, 1, 0)

    def _newAction(self, relation: Relation, row: int, col: int) -> QAction:
        action_ = action(relation.text, IconRegistry.from_name(relation.icon, relation.icon_color))
        self.addAction(action_, row, col)
        action_.triggered.connect(lambda: self.relationSelected.emit(relation))

        return action_


class ConnectorEditor(BaseItemEditor):
    def __init__(self, network: RelationsNetwork, parent=None):
        super().__init__(parent)
        self._connector: Optional[ConnectorItem] = None

        self._btnRelationType = RelationsButton()
        self._btnColor = tool_btn(IconRegistry.from_name('fa5s.circle', color='darkBlue'), 'Change style',
                                  transparent_=True)
        self._colorPicker = ColorPicker(self, maxColumn=5)
        self._colorPicker.colorPicked.connect(self._colorChanged)
        self._colorSecondaryWidget = SecondarySelectorWidget(self)
        self._colorSecondaryWidget.addWidget(self._colorPicker, 0, 0)
        self.addSecondaryWidget(self._btnColor, self._colorSecondaryWidget)
        self._btnIcon = tool_btn(IconRegistry.from_name('mdi.emoticon-outline'), 'Change icon', transparent_=True)
        self._btnIcon.clicked.connect(self._showIconSelector)

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

        self._relationSelector = RelationSelector(network, self._btnRelationType)
        self._relationSelector.relationSelected.connect(self._relationChanged)

        self._toolbar.layout().addWidget(self._btnRelationType)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._btnColor)
        self._toolbar.layout().addWidget(self._btnIcon)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._solidLine)
        self._toolbar.layout().addWidget(self._dashLine)
        self._toolbar.layout().addWidget(self._dotLine)
        self._toolbar.layout().addWidget(vline())
        self._toolbar.layout().addWidget(self._sbWidth)

    def setItem(self, connector: ConnectorItem):
        self._connector = None
        self._hideSecondarySelectors()

        self._sbWidth.setValue(connector.penWidth())
        relation = connector.relation()
        # if relation:
        #     self._relationSelector.selectRelation(relation)
        # else:
        #     self._relationSelector.reset()

        penStyle = connector.penStyle()
        for line in [self._solidLine, self._dashLine, self._dotLine]:
            if penStyle == line.penStyle():
                line.setChecked(True)
                break
        self._connector = connector

    def _relationChanged(self, relation: Relation):
        if self._connector:
            self._connector.setRelation(relation)

    def _penStyleChanged(self):
        btn = self._lineBtnGroup.checkedButton()
        if btn and self._connector:
            self._connector.setPenStyle(btn.penStyle())

    def _widthChanged(self, value: int):
        if self._connector:
            self._connector.setPenWidth(value)

    def _colorChanged(self, color: QColor):
        if self._connector:
            self._connector.setColor(color)
            pass

    def _showIconSelector(self):
        result = IconSelectorDialog().display()
        if result and self._connector:
            self._connector.setIcon(result[0])
