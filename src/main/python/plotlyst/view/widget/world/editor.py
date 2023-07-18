from functools import partial
from typing import Optional, Dict, Set

from PyQt6.QtCore import pyqtSignal
from qthandy import vspacer, clear_layout

from src.main.python.plotlyst.common import recursive
from src.main.python.plotlyst.core.domain import Novel, WorldBuildingEntity
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.tree import TreeView, ContainerNode, TreeSettings


class EntityNode(ContainerNode):
    def __init__(self, entity: WorldBuildingEntity, parent=None, settings: Optional[TreeSettings] = None):
        super(EntityNode, self).__init__(entity.name, parent=parent, settings=settings)
        self._entity = entity
        self.setPlusButtonEnabled(True)
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
        # self._btnAdd.setIcon(IconRegistry.plus_icon(PLOTLYST_MAIN_COLOR))
        # self._btnAdd.clicked.connect(self.newNovelRequested.emit)


class WorldBuildingTreeView(TreeView):
    entitySelected = pyqtSignal(WorldBuildingEntity)

    def __init__(self, parent=None, settings: Optional[TreeSettings] = None):
        super(WorldBuildingTreeView, self).__init__(parent)
        self._novel: Optional[Novel] = None
        self._settings: Optional[TreeSettings] = settings
        self._root: Optional[RootNode] = None
        self._entities: Dict[WorldBuildingEntity, EntityNode] = {}
        self._selectedEntities: Set[WorldBuildingEntity] = set()

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

    def __initEntityWidget(self, entity: WorldBuildingEntity) -> EntityNode:
        node = EntityNode(entity, settings=self._settings)
        node.selectionChanged.connect(partial(self._entitySelectionChanged, node))

        self._entities[entity] = node
        return node
