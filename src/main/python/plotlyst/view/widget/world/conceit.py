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
from functools import partial
from typing import Optional, List, Dict

from PyQt6.QtCore import pyqtSignal
from overrides import overrides
from qthandy import clear_layout, vspacer

from plotlyst.common import recursive
from plotlyst.core.domain import WorldConceit, WorldBuilding, WorldConceitType, Novel
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.tree import ItemBasedNode, TreeSettings, ItemBasedTreeView, ContainerNode


class ConceitNode(ItemBasedNode):
    added = pyqtSignal()

    def __init__(self, conceit: WorldConceit, parent=None, readOnly: bool = False,
                 settings: Optional[TreeSettings] = None):
        super().__init__(conceit.name, parent=parent, settings=settings)
        self._conceit = conceit
        self.setPlusButtonEnabled(not readOnly)
        self.setMenuEnabled(not readOnly)
        self.setTranslucentIconEnabled(True)
        self._actionChangeIcon.setVisible(False)
        self._btnAdd.clicked.connect(self.added)
        self.refresh()

    @overrides
    def item(self) -> WorldConceit:
        return self._conceit

    @overrides
    def refresh(self):
        self._lblTitle.setText(self._conceit.name if self._conceit.name else 'Conceit')
        if self._conceit.icon:
            self._icon.setIcon(IconRegistry.from_name(self._conceit.icon))
        else:
            self._icon.setIcon(IconRegistry.dot_icon())

    @overrides
    def _iconChanged(self, iconName: str, iconColor: str):
        pass


# class ConceitRootNode(ContainerNode):
#     def __init__(self, parent=None):
#         super().__init__('Conceits', parent, readOnly=True)


class ConceitTypeNode(ContainerNode):
    def __init__(self, conceitType: WorldConceitType, parent=None):
        super().__init__(conceitType.name, IconRegistry.from_name(conceitType.icon()), parent, readOnly=True)


class ConceitsTreeView(ItemBasedTreeView):
    CONCEIT_ENTITY_MIMETYPE = 'application/world-conceit'
    conceitSelected = pyqtSignal(WorldConceit)
    conceitDeleted = pyqtSignal(WorldConceit)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._world: WorldBuilding = novel.world
        self._readOnly = False
        self._settings = TreeSettings(bg_color='#ede0d4',
                                      action_buttons_color='#510442',
                                      selection_bg_color='#DABFA7',
                                      hover_bg_color='#E3D0BD',
                                      selection_text_color='#510442')
        self._centralWidget.setStyleSheet(f'#centralWidget {{background: {self._settings.bg_color};}}')

        self.repo = RepositoryPersistenceManager.instance()

        self.refresh()

    def refresh(self):
        def addChildWdg(parent: WorldConceit, child: WorldConceit):
            childWdg = self._initNode(child)
            self._nodes[parent].addChild(childWdg)

        self.clearSelection()
        self._nodes.clear()
        clear_layout(self._centralWidget)

        rootNode = ContainerNode('Conceits', readOnly=True)
        self._centralWidget.layout().addWidget(rootNode)

        typeNodes: Dict[WorldConceitType, ContainerNode] = {}
        for conceitType in WorldConceitType:
            typeNode = ContainerNode(conceitType.name, IconRegistry.from_name(conceitType.icon()), readOnly=True)
            typeNodes[conceitType] = typeNode
            rootNode.addChild(typeNode)

        for conceit in self._world.conceits:
            node = self._initNode(conceit)
            typeNodes[conceit.type].addChild(node)
            recursive(conceit, lambda parent: parent.children, addChildWdg)
        self._centralWidget.layout().addWidget(vspacer())

        for node in typeNodes.values():
            if not node.childrenWidgets():
                node.setVisible(False)

    @overrides
    def _emitSelectionChanged(self, conceit: WorldConceit):
        self.conceitSelected.emit(conceit)

    @overrides
    def _mimeType(self) -> str:
        return self.CONCEIT_ENTITY_MIMETYPE

    @overrides
    def _topLevelItems(self) -> List[WorldConceit]:
        return self._world.conceits

    @overrides
    def _node(self, conceit: WorldConceit) -> ConceitNode:
        return ConceitNode(conceit, settings=self._settings)

    @overrides
    def _save(self):
        self.repo.update_world(self._novel)

    @overrides
    def _initNode(self, conceit: WorldConceit) -> ConceitNode:
        node = ConceitNode(conceit, readOnly=self._readOnly, settings=self._settings)
        self._nodes[conceit] = node
        node.selectionChanged.connect(partial(self._selectionChanged, node))
        # node.added.connect(partial(self._addLocationUnder, node))
        # node.deleted.connect(partial(self._deleteLocation, node))

        # if not self._readOnly:
        #     self._enhanceWithDnd(node)

        return node
