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

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import QButtonGroup
from overrides import overrides
from qthandy import vline, retain_when_hidden
from qtmenu import GridMenuWidget

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Diagram, Relation, Node
from src.main.python.plotlyst.core.domain import Novel, Character, DiagramNodeType
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.common import tool_btn, action
from src.main.python.plotlyst.view.dialog.utility import IconSelectorDialog
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorMenu
from src.main.python.plotlyst.view.widget.graphics import BaseItemEditor, SolidPenStyleSelector, DashPenStyleSelector, \
    DotPenStyleSelector, ConnectorItem, PenWidthEditor, RelationsButton, SecondarySelectorWidget, CharacterItem
from src.main.python.plotlyst.view.widget.graphics import NodeItem, NetworkGraphicsView, NetworkScene
from src.main.python.plotlyst.view.widget.utility import ColorPicker


class RelationsEditorScene(NetworkScene):
    def __init__(self, novel: Novel, parent=None):
        super(RelationsEditorScene, self).__init__(parent)
        self._novel = novel

        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def _character(self, node: Node) -> Optional[Character]:
        return node.character(self._novel) if node.character_id else None

    @overrides
    def _load(self):
        json_client.load_diagram(self._novel, self._diagram)

    @overrides
    def _save(self):
        self.repo.update_diagram(self._novel, self._diagram)


class CharacterNetworkView(NetworkGraphicsView):
    def __init__(self, novel: Novel, parent=None):
        self._novel = novel
        super(CharacterNetworkView, self).__init__(parent)

        self._btnAddCharacter = self._newControlButton(IconRegistry.character_icon('#040406'), 'Add new character',
                                                       DiagramNodeType.CHARACTER)
        self._btnAddSticker = self._newControlButton(IconRegistry.from_name('mdi6.sticker-circle-outline'),
                                                     'Add new sticker', DiagramNodeType.STICKER)

        self._connectorEditor = ConnectorEditor(self)
        self._connectorEditor.setVisible(False)

        self._scene.selectionChanged.connect(self._selectionChanged)

    @overrides
    def _initScene(self) -> NetworkScene:
        return RelationsEditorScene(self._novel)

    def refresh(self):
        if not self._diagram:
            self.setDiagram(self._novel.character_networks[0])
            self._connectorEditor.setNetwork(self._diagram)

    def relationsScene(self) -> RelationsEditorScene:
        return self._scene

    @overrides
    def _startAddition(self, itemType: DiagramNodeType):
        super()._startAddition(itemType)
        self._scene.startAdditionMode(itemType)

    @overrides
    def _endAddition(self, itemType: Optional[DiagramNodeType] = None, item: Optional[NodeItem] = None):
        super()._endAddition(itemType, item)
        if itemType == DiagramNodeType.CHARACTER:
            QTimer.singleShot(100, lambda: self._finishCharacterAddition(item))

    def _finishCharacterAddition(self, item: CharacterItem):
        def select(character: Character):
            item.setCharacter(character)

        popup = CharacterSelectorMenu(self._novel, parent=self)
        popup.selected.connect(select)
        view_pos = self.mapFromScene(item.sceneBoundingRect().topRight())
        popup.exec(self.mapToGlobal(view_pos))

    def _selectionChanged(self):
        items = self._scene.selectedItems()
        if len(items) == 1 and isinstance(items[0], ConnectorItem):
            self._connectorSelected(items[0])
        else:
            self._connectorEditor.setVisible(False)

    def _connectorSelected(self, connector: ConnectorItem):
        self._connectorEditor.setItem(connector)
        self._popupAbove(self._connectorEditor, connector)


class RelationSelector(GridMenuWidget):
    relationSelected = pyqtSignal(Relation)

    def __init__(self, network: Diagram = None, parent=None):
        super().__init__(parent)
        self._network = network
        self._romance = Relation('Romance', icon='ei.heart', icon_color='#d1495b')
        self._breakUp = Relation('Breakup', icon='fa5s.heart-broken', icon_color='#d1495b')
        self._affection = Relation('Affection', icon='mdi.sparkles', icon_color='#d1495b')
        self._crush = Relation('Crush', icon='fa5.grin-hearts', icon_color='#d1495b')
        self._unrequited = Relation('Unrequited love', icon='mdi.heart-half-full', icon_color='#d1495b')

        self._colleague = Relation('Colleague', icon='fa5s.briefcase', icon_color='#9c6644')
        self._student = Relation('Student', icon='fa5s.graduation-cap', icon_color='black')
        self._foil = Relation('Foil', icon='fa5s.yin-yang', icon_color='#947eb0')

        self._friendship = Relation('Friendship', icon='fa5s.user-friends', icon_color='#457b9d')
        self._sidekick = Relation('Sidekick', icon='ei.asl', icon_color='#b0a990')
        self._guide = Relation('Guide', icon='mdi.compass-rose', icon_color='#80ced7')
        self._supporter = Relation('Supporter', icon='fa5s.thumbs-up', icon_color='#266dd3')
        self._adversary = Relation('Adversary', icon='fa5s.thumbs-down', icon_color='#9e1946')
        self._betrayal = Relation('Betrayal', icon='mdi6.knife', icon_color='grey')
        self._conflict = Relation('Conflict', icon='mdi.sword-cross', icon_color='#f3a712')

        self._newAction(self._romance, 0, 0)
        self._newAction(self._affection, 0, 1)
        self._newAction(self._crush, 0, 2)
        self._newAction(self._breakUp, 1, 0)
        self._newAction(self._unrequited, 1, 1, 2)
        self.addSeparator(2, 0, colSpan=3)
        self._newAction(self._friendship, 3, 0)
        self._newAction(self._sidekick, 3, 1)
        self._newAction(self._guide, 3, 2)
        self._newAction(self._supporter, 4, 0)
        self._newAction(self._adversary, 4, 1)
        self._newAction(self._betrayal, 5, 0)
        self._newAction(self._conflict, 5, 1)
        self._newAction(self._foil, 6, 0)
        self.addSeparator(7, 0, colSpan=3)
        self._newAction(self._colleague, 8, 0)
        self._newAction(self._student, 8, 1)

    def _newAction(self, relation: Relation, row: int, col: int, colSpan: int = 1, showText: bool = True) -> QAction:
        text = relation.text if showText else ''
        action_ = action(text, IconRegistry.from_name(relation.icon, relation.icon_color))
        action_.setToolTip(relation.text)
        self.addAction(action_, row, col, colSpan=colSpan)
        action_.triggered.connect(lambda: self.relationSelected.emit(relation))

        return action_


class ConnectorEditor(BaseItemEditor):
    def __init__(self, parent=None):
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

        self._relationSelector: Optional[RelationSelector] = None

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

    def setNetwork(self, diagram: Diagram):
        self._relationSelector = RelationSelector(diagram, self._btnRelationType)
        self._relationSelector.relationSelected.connect(self._relationChanged)

    def setItem(self, connector: ConnectorItem):
        self._connector = None
        self._hideSecondarySelectors()

        self._sbWidth.setValue(connector.penWidth())

        icon: str = connector.icon()
        self._updateColor(connector.color().name())
        if icon:
            self._updateIcon(icon)
        else:
            self._resetIcon()

        penStyle = connector.penStyle()
        for line in [self._solidLine, self._dashLine, self._dotLine]:
            if penStyle == line.penStyle():
                line.setChecked(True)
                break
        self._connector = connector

    def _relationChanged(self, relation: Relation):
        if self._connector:
            self._connector.setRelation(relation)
            self._updateIcon(relation.icon)
            self._updateColor(relation.icon_color)

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
            self._updateColor(color.name())
            pass

    def _showIconSelector(self):
        dialog = IconSelectorDialog()
        retain_when_hidden(dialog.selector.colorPicker)
        dialog.selector.colorPicker.setVisible(False)
        result = dialog.display()
        if result and self._connector:
            self._connector.setIcon(result[0])
            self._updateIcon(result[0])

    def _updateIcon(self, icon: str):
        self._btnIcon.setIcon(IconRegistry.from_name(icon))

    def _resetIcon(self):
        self._btnIcon.setIcon(IconRegistry.from_name('mdi.emoticon-outline'))

    def _updateColor(self, color: str):
        self._btnColor.setIcon(IconRegistry.from_name('fa5s.circle', color))
