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

from PyQt6.QtCore import pyqtSignal, QMimeData, Qt, QPointF
from qthandy import vspacer, clear_layout, transparent, translucent, gc
from qthandy.filter import DragEventFilter, DropEventFilter
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

        main_section = WorldBuildingEntityElement(WorldBuildingEntityElementType.Main_Section)
        main_section.blocks.append(WorldBuildingEntityElement(WorldBuildingEntityElementType.Header))
        main_section.blocks.append(WorldBuildingEntityElement(WorldBuildingEntityElementType.Text))
        entity = WorldBuildingEntity(name, icon=icon_name, type=wdType,
                                     elements=[main_section])

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
    WORLD_ENTITY_MIMETYPE = 'application/world-entity'
    entitySelected = pyqtSignal(WorldBuildingEntity)

    def __init__(self, parent=None, settings: Optional[TreeSettings] = None):
        super(WorldBuildingTreeView, self).__init__(parent)
        self._novel: Optional[Novel] = None
        self._settings: Optional[TreeSettings] = settings
        self._root: Optional[RootNode] = None
        self._entities: Dict[WorldBuildingEntity, EntityNode] = {}
        self._selectedEntities: Set[WorldBuildingEntity] = set()
        transparent(self)

        self._dummyWdg: Optional[EntityNode] = None
        self._toBeRemoved: Optional[EntityNode] = None

        self.repo = RepositoryPersistenceManager.instance()

    def selectRoot(self):
        self._root.select()
        self._entitySelectionChanged(self._root, self._root.isSelected())

    def setSettings(self, settings: TreeSettings):
        self._settings = settings
        self._centralWidget.setStyleSheet(f'#centralWidget {{background: {settings.bg_color};}}')

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

    def _dragStarted(self, wdg: EntityNode):
        wdg.setHidden(True)
        self._dummyWdg = EntityNode(wdg.entity(), settings=self._settings)
        self._dummyWdg.setPlusButtonEnabled(False)
        self._dummyWdg.setMenuEnabled(False)
        translucent(self._dummyWdg)
        self._dummyWdg.setHidden(True)
        self._dummyWdg.setParent(self._centralWidget)
        self._dummyWdg.setAcceptDrops(True)
        self._dummyWdg.installEventFilter(
            DropEventFilter(self._dummyWdg, [self.WORLD_ENTITY_MIMETYPE], droppedSlot=self._drop))

    def _dragStopped(self, wdg: EntityNode):
        if self._dummyWdg:
            gc(self._dummyWdg)
            self._dummyWdg = None

        if self._toBeRemoved:
            gc(self._toBeRemoved)
            self._toBeRemoved = None
        else:
            wdg.setVisible(True)

    def _dragMovedOnEntity(self, wdg: EntityNode, edge: Qt.Edge, point: QPointF):
        i = wdg.parent().layout().indexOf(wdg)
        if edge == Qt.Edge.TopEdge:
            wdg.parent().layout().insertWidget(i, self._dummyWdg)
        elif point.x() > 50:
            wdg.insertChild(0, self._dummyWdg)
        else:
            wdg.parent().layout().insertWidget(i + 1, self._dummyWdg)

        self._dummyWdg.setVisible(True)

    def _drop(self, mimeData: QMimeData):
        self.clearSelection()

        if self._dummyWdg.isHidden():
            return
        ref: WorldBuildingEntity = mimeData.reference()
        self._toBeRemoved = self._entities[ref]
        new_widget = self.__initEntityWidget(ref)
        for child in self._toBeRemoved.childrenWidgets():
            new_widget.addChild(child)

        entity_parent_wdg: EntityNode = self._dummyWdg.parent().parent()
        new_index = entity_parent_wdg.containerWidget().layout().indexOf(self._dummyWdg)
        if self._toBeRemoved.parent() is not self._centralWidget and \
                self._toBeRemoved.parent().parent() is self._dummyWdg.parent().parent():  # swap under same parent doc
            old_index = entity_parent_wdg.indexOf(self._toBeRemoved)
            entity_parent_wdg.entity().children.remove(ref)
            if old_index < new_index:
                entity_parent_wdg.entity().children.insert(new_index - 1, ref)
            else:
                entity_parent_wdg.entity().children.insert(new_index, ref)
        else:
            self._removeFromParentEntity(ref, self._toBeRemoved)
            entity_parent_wdg.entity().children.insert(new_index, ref)

        entity_parent_wdg.insertChild(new_index, new_widget)

        self._dummyWdg.setHidden(True)
        self.repo.update_world(self._novel)

    def _removeFromParentEntity(self, entity: WorldBuildingEntity, wdg: EntityNode):
        parent: EntityNode = wdg.parent().parent()
        parent.entity().children.remove(entity)

    def __initEntityWidget(self, entity: WorldBuildingEntity) -> EntityNode:
        node = EntityNode(entity, settings=self._settings)
        node.selectionChanged.connect(partial(self._entitySelectionChanged, node))
        node.addEntity.connect(partial(self._addEntity, node))
        node.deleted.connect(partial(self._removeEntity, node))

        node.installEventFilter(
            DragEventFilter(node, self.WORLD_ENTITY_MIMETYPE, dataFunc=lambda node: node.entity(),
                            grabbed=node.titleLabel(),
                            startedSlot=partial(self._dragStarted, node),
                            finishedSlot=partial(self._dragStopped, node)))
        node.titleWidget().setAcceptDrops(True)
        node.titleWidget().installEventFilter(
            DropEventFilter(node, [self.WORLD_ENTITY_MIMETYPE],
                            motionDetection=Qt.Orientation.Vertical,
                            motionSlot=partial(self._dragMovedOnEntity, node),
                            droppedSlot=self._drop
                            )
        )

        self._entities[entity] = node
        return node
