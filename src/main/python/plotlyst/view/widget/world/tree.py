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
from typing import Optional, Dict, Set

from PyQt6.QtCore import pyqtSignal
from qthandy import vspacer, clear_layout, transparent
from qtmenu import MenuWidget

from plotlyst.common import recursive
from plotlyst.core.domain import Novel, WorldBuildingEntity, WorldBuildingEntityType, \
    WorldBuildingEntityElement, WorldBuildingEntityElementType
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.common import action, fade_out_and_gc
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.tree import TreeView, ContainerNode, TreeSettings


class EntityAdditionMenu(MenuWidget):
    entityTriggered = pyqtSignal(WorldBuildingEntity)

    def __init__(self, parent=None):
        super(EntityAdditionMenu, self).__init__(parent)
        self.addAction(action('Entity', IconRegistry.world_building_icon(),
                              slot=lambda: self._triggered(WorldBuildingEntityType.ABSTRACT),
                              tooltip='Any physical, human, or abstract entity in the world, e.g., location, kingdom, magic, God, etc.'))
        self.addSeparator()

        submenu = MenuWidget()
        submenu.setTitle('Link')
        submenu.setIcon(IconRegistry.from_name('fa5s.link'))
        submenu.setDisabled(True)
        submenu.addAction(action('Location', IconRegistry.location_icon()))
        submenu.addAction(action('Social group', IconRegistry.group_icon()))
        submenu.addAction(action('Character', IconRegistry.character_icon()))

        self.addMenu(submenu)

    def _triggered(self, wdType: WorldBuildingEntityType):
        if wdType == WorldBuildingEntityType.SETTING:
            name = 'New location'
            icon_name = 'fa5s.map-pin'
        elif wdType == WorldBuildingEntityType.GROUP:
            name = 'New group'
            icon_name = 'mdi.account-group'
        elif wdType == WorldBuildingEntityType.ITEM:
            name = 'New item'
            icon_name = ''
        elif wdType == WorldBuildingEntityType.CONTAINER:
            name = 'Container'
            icon_name = ''
        else:
            name = 'New entity'
            icon_name = ''

        entity = WorldBuildingEntity(name, icon=icon_name, type=wdType,
                                     elements=[WorldBuildingEntityElement(WorldBuildingEntityElementType.Text)])

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
        self._centralWidget.setStyleSheet('background: #ede0d4;')
        transparent(self)

        self.repo = RepositoryPersistenceManager.instance()

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
        self._novel.world.root_entity.children.append(entity)
        self.repo.update_world(self._novel)

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
        self.repo.update_world(self._novel)

    def _removeEntity(self, node: EntityNode):
        entity = node.entity()
        self.clearSelection()
        self.selectRoot()

        node.parent().parent().entity().children.remove(entity)
        fade_out_and_gc(node.parent(), node)
        self.repo.update_world(self._novel)

    def __initEntityWidget(self, entity: WorldBuildingEntity) -> EntityNode:
        node = EntityNode(entity, settings=self._settings)
        node.selectionChanged.connect(partial(self._entitySelectionChanged, node))
        node.addEntity.connect(partial(self._addEntity, node))
        node.deleted.connect(partial(self._removeEntity, node))

        self._entities[entity] = node
        return node
