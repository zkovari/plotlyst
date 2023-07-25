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
from functools import partial
from typing import Optional, Dict, Set

from PyQt6.QtCore import pyqtSignal
from qthandy import vspacer, clear_layout
from qtmenu import MenuWidget, ActionTooltipDisplayMode

from src.main.python.plotlyst.common import recursive
from src.main.python.plotlyst.core.domain import Novel, WorldBuildingEntity, WorldBuildingEntityType
from src.main.python.plotlyst.view.common import action
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode, TreeSettings


class EntityAdditionMenu(MenuWidget):
    entityTriggered = pyqtSignal(WorldBuildingEntity)

    def __init__(self, parent=None):
        super(EntityAdditionMenu, self).__init__(parent)
        self.setTooltipDisplayMode(ActionTooltipDisplayMode.DISPLAY_UNDER)

        self.addAction(action('Location', IconRegistry.location_icon(),
                              slot=lambda: self._triggered(WorldBuildingEntityType.SETTING),
                              tooltip='Physical location in the world'))
        self.addAction(action('Entity', IconRegistry.world_building_icon(),
                              slot=lambda: self._triggered(WorldBuildingEntityType.ABSTRACT),
                              tooltip='Abstract entity in the world, e.g., magic'))
        self.addAction(action('Social group', IconRegistry.group_icon(),
                              slot=lambda: self._triggered(WorldBuildingEntityType.GROUP),
                              tooltip='Social group in the world, e.g., a guild or an organization'))
        self.addSeparator()
        self.addAction(action('Item', IconRegistry.from_name('mdi.ring', '#b6a6ca'),
                              slot=lambda: self._triggered(WorldBuildingEntityType.ITEM),
                              tooltip='Relevant item in the world, e.g., an artifact'))
        self.addSeparator()
        self.addAction(action('Container',
                              slot=lambda: self._triggered(WorldBuildingEntityType.CONTAINER),
                              tooltip='General container to group worldbuilding entities together'))

    def _triggered(self, wdType: WorldBuildingEntityType):
        if wdType == WorldBuildingEntityType.SETTING:
            name = 'New location'
            icon_name = 'fa5s.map-pin'
        elif wdType == WorldBuildingEntityType.GROUP:
            name = 'New group'
            icon_name = 'mdi.account-group'
        elif wdType == WorldBuildingEntityType.ITEM:
            name = 'New item'
        elif wdType == WorldBuildingEntityType.CONTAINER:
            name = 'Container'
        else:
            name = 'New entity'
            icon_name = ''

        entity = WorldBuildingEntity(name, icon=icon_name, type=wdType)

        self.entityTriggered.emit(entity)


class EntityNode(ContainerNode):
    addEntity = pyqtSignal(WorldBuildingEntity)

    def __init__(self, entity: WorldBuildingEntity, parent=None, settings: Optional[TreeSettings] = None):
        super(EntityNode, self).__init__(entity.name, parent=parent, settings=settings)
        self._entity = entity
        self.setPlusButtonEnabled(True)
        self._additionMenu = EntityAdditionMenu(self._btnAdd)
        self._additionMenu.entityTriggered.connect(self.addEntity.emit)
        self.setPlusMenu(self._additionMenu)
        self.refresh()

    def entity(self) -> WorldBuildingEntity:
        return self._entity

    def refresh(self):
        self._lblTitle.setText(self._entity.name)

        if self._entity.icon:
            self._icon.setIcon(IconRegistry.from_name(self._entity.icon, self._entity.icon_color))
            self._icon.setVisible(True)
        else:
            self._icon.setHidden(True)


class RootNode(EntityNode):

    def __init__(self, entity: WorldBuildingEntity, parent=None, settings: Optional[TreeSettings] = None):
        super(RootNode, self).__init__(entity, parent=parent, settings=settings)
        self.setMenuEnabled(False)
        self.setPlusButtonEnabled(False)


class WorldBuildingTreeView(TreeView):
    entitySelected = pyqtSignal(WorldBuildingEntity)

    def __init__(self, parent=None, settings: Optional[TreeSettings] = None):
        super(WorldBuildingTreeView, self).__init__(parent)
        self._novel: Optional[Novel] = None
        self._settings: Optional[TreeSettings] = settings
        self._root: Optional[RootNode] = None
        self._entities: Dict[WorldBuildingEntity, EntityNode] = {}
        self._selectedEntities: Set[WorldBuildingEntity] = set()
        self._centralWidget.setProperty('bg', True)

    def selectRoot(self):
        self._root.select()
        self._entitySelectionChanged(self._root, self._root.isSelected())

    def setSettings(self, settings: TreeSettings):
        self._settings = settings

    def setNovel(self, novel: Novel):
        self._novel = novel
        self._root = RootNode(self._novel.world.root_entity, settings=self._settings)
        self._root.selectionChanged.connect(partial(self._entitySelectionChanged, self._root))
        self.refresh()

    def addEntity(self, entity: WorldBuildingEntity):
        wdg = self.__initEntityWidget(entity)
        self._root.addChild(wdg)

    def refresh(self):
        def addChildWdg(parent: WorldBuildingEntity, child: WorldBuildingEntity):
            childWdg = self.__initEntityWidget(child)
            self._entities[parent].addChild(childWdg)

        self.clearSelection()
        self._entities.clear()
        clear_layout(self._centralWidget)

        self._entities[self._novel.world.root_entity] = self._root
        self._centralWidget.layout().addWidget(self._root)
        for entity in self._novel.world.root_entity.children:
            wdg = self.__initEntityWidget(entity)
            self._root.addChild(wdg)
            recursive(entity, lambda parent: parent.children, addChildWdg)
        self._centralWidget.layout().addWidget(vspacer())

    def updateEntity(self, entity: WorldBuildingEntity):
        self._entities[entity].refresh()

    def clearSelection(self):
        for entity in self._selectedEntities:
            self._entities[entity].deselect()
        self._selectedEntities.clear()

    def _entitySelectionChanged(self, node: EntityNode, selected: bool):
        if selected:
            self.clearSelection()
            self._selectedEntities.add(node.entity())
            self.entitySelected.emit(node.entity())
        elif node.entity() in self._selectedEntities:
            self._selectedEntities.remove(node.entity())

    def _addEntity(self, parent: EntityNode, entity: WorldBuildingEntity):
        wdg = self.__initEntityWidget(entity)
        parent.addChild(wdg)
        parent.entity().children.append(entity)

    def __initEntityWidget(self, entity: WorldBuildingEntity) -> EntityNode:
        node = EntityNode(entity, settings=self._settings)
        node.selectionChanged.connect(partial(self._entitySelectionChanged, node))
        node.addEntity.connect(partial(self._addEntity, node))

        self._entities[entity] = node
        return node
