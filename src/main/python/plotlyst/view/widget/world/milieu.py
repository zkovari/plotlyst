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
from typing import Optional, List

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QLineEdit
from overrides import overrides
from qthandy import vbox, incr_font, vspacer, line, clear_layout

from plotlyst.common import recursive
from plotlyst.core.domain import Novel, Location, WorldBuildingEntity
from plotlyst.event.core import emit_event
from plotlyst.events import LocationAddedEvent, LocationDeletedEvent, \
    RequestMilieuDictionaryResetEvent
from plotlyst.service.cache import entities_registry
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.common import fade_in, insert_before_the_end, DelayedSignalSlotConnector
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.confirm import confirmed
from plotlyst.view.widget.input import DecoratedTextEdit
from plotlyst.view.widget.tree import TreeSettings, ItemBasedTreeView, ItemBasedNode


class LocationNode(ItemBasedNode):
    added = pyqtSignal()

    def __init__(self, location: Location, parent=None, readOnly: bool = False,
                 settings: Optional[TreeSettings] = None):
        super().__init__(location.name, parent=parent, settings=settings)
        self._location = location
        self.setPlusButtonEnabled(not readOnly)
        self.setMenuEnabled(not readOnly)
        self.setTranslucentIconEnabled(True)
        self._actionChangeIcon.setVisible(False)
        self._btnAdd.clicked.connect(self.added)
        self.refresh()

    @overrides
    def item(self) -> Location:
        return self._location

    @overrides
    def refresh(self):
        self._lblTitle.setText(self._location.name if self._location.name else 'Location')
        # if self._novel.icon:
        #     self._icon.setIcon(IconRegistry.from_name(self._novel.icon, self._novel.icon_color))
        # else:
        self._icon.setIcon(IconRegistry.location_icon('black'))
        self._icon.setVisible(True)

    @overrides
    def _iconChanged(self, iconName: str, iconColor: str):
        print('icon changed')
        pass
        # self._novel.icon = iconName
        # self._novel.icon_color = iconColor


class LocationsTreeView(ItemBasedTreeView):
    LOCATION_ENTITY_MIMETYPE = 'application/milieu-location'
    locationSelected = pyqtSignal(Location)
    locationDeleted = pyqtSignal(Location)
    updateWorldBuildingEntity = pyqtSignal(WorldBuildingEntity)
    unlinkWorldBuildingEntity = pyqtSignal(WorldBuildingEntity)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel: Optional[Novel] = None
        self._readOnly = False
        self._settings = TreeSettings(font_incr=2)

        self.repo = RepositoryPersistenceManager.instance()

    def setNovel(self, novel: Novel, readOnly: bool = False):
        def addChildWdg(parent: Location, child: Location):
            childWdg = self._initNode(child)
            self._nodes[parent].addChild(childWdg)

        self._novel = novel
        self._readOnly = readOnly

        self.clearSelection()
        self._nodes.clear()

        clear_layout(self._centralWidget)
        for location in self._novel.locations:
            node = self._initNode(location)
            self._centralWidget.layout().addWidget(node)
            recursive(location, lambda parent: parent.children, addChildWdg)
        self._centralWidget.layout().addWidget(vspacer())

        if self._novel.locations:
            node = self._nodes[self._novel.locations[0]]
            node.select()
            self._selectionChanged(node, True)

    @overrides
    def updateItem(self, location: Location):
        super().updateItem(location)
        for ref in entities_registry.refs(location):
            if isinstance(ref, WorldBuildingEntity):
                self.updateWorldBuildingEntity.emit(ref)

    def addNewLocation(self):
        location = Location()
        node = self._initNode(location)
        insert_before_the_end(self._centralWidget, node)
        node.select()
        self._selectionChanged(node, node.isSelected())

        self._novel.locations.append(location)
        self._save()

        emit_event(self._novel, LocationAddedEvent(self, location))

    def _addLocationUnder(self, node: LocationNode):
        location = Location()
        child = self._initNode(location)
        node.addChild(child)
        fade_in(child)

        node.item().children.append(location)
        self._save()
        emit_event(self._novel, LocationAddedEvent(self, location))

    def _deleteLocation(self, node: LocationNode):
        loc: Location = node.item()
        title = f'Are you sure you want to delete the location "{loc.name if loc.name else "Untitled"}"?'
        msg = 'This action cannot be undone, and the location and all its references will be lost.'
        if not confirmed(msg, title):
            return

        if isinstance(node.parent().parent(), LocationNode):
            parent: LocationNode = node.parent().parent()
            parent.item().children.remove(loc)
        else:
            self._novel.locations.remove(loc)

        self._deleteNode(node)
        self.locationDeleted.emit(loc)

        for ref in entities_registry.refs(loc):
            if isinstance(ref, WorldBuildingEntity):
                self.unlinkWorldBuildingEntity.emit(ref)

        self._save()
        emit_event(self._novel, LocationDeletedEvent(self, loc))

    @overrides
    def _emitSelectionChanged(self, location: Location):
        self.locationSelected.emit(location)

    @overrides
    def _mimeType(self) -> str:
        return self.LOCATION_ENTITY_MIMETYPE

    @overrides
    def _topLevelItems(self) -> List[Location]:
        return self._novel.locations

    @overrides
    def _node(self, location: Location) -> LocationNode:
        return LocationNode(location, settings=self._settings)

    @overrides
    def _save(self):
        self.repo.update_novel(self._novel)

    @overrides
    def _removeFromParentEntity(self, location: Location, node: LocationNode):
        if node.parent() is self._centralWidget:
            self._novel.locations.remove(location)
        else:
            super()._removeFromParentEntity(location, node)

    @overrides
    def _initNode(self, location: Location) -> LocationNode:
        node = LocationNode(location, readOnly=self._readOnly, settings=self._settings)
        self._nodes[location] = node
        node.selectionChanged.connect(partial(self._selectionChanged, node))
        node.added.connect(partial(self._addLocationUnder, node))
        node.deleted.connect(partial(self._deleteLocation, node))

        if not self._readOnly:
            self._enhanceWithDnd(node)

        return node


class LocationEditor(QWidget):
    locationNameChanged = pyqtSignal(Location)

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._location: Optional[Location] = None

        self.lineEditName = QLineEdit()
        self.lineEditName.setPlaceholderText('Location name')
        self.lineEditName.setProperty('transparent', True)
        incr_font(self.lineEditName, 8)
        self.lineEditName.textEdited.connect(self._nameEdited)
        DelayedSignalSlotConnector(self.lineEditName.textEdited, self._nameSet, parent=self)

        self.textSummary = DecoratedTextEdit()
        self.textSummary.setProperty('rounded', True)
        self.textSummary.setProperty('white-bg', True)
        self.textSummary.setPlaceholderText('Summarize this location')
        self.textSummary.setMaximumSize(450, 85)
        self.textSummary.setToolTip('Summary')
        self.textSummary.setEmoji(':scroll:', 'Summary')
        self.textSummary.textChanged.connect(self._summaryChanged)

        vbox(self)
        self.layout().addWidget(self.lineEditName)
        self.layout().addWidget(line())
        self.layout().addWidget(self.textSummary)
        self.layout().addWidget(vspacer())

        self.repo = RepositoryPersistenceManager.instance()

        self.setVisible(False)

    def setLocation(self, location: Location):
        self.setVisible(True)
        self._location = location
        self.lineEditName.setText(self._location.name)
        self.textSummary.setText(self._location.summary)
        if not self._location.name:
            self.lineEditName.setFocus()

    def locationDeletedEvent(self, location: Location):
        if location is self._location:
            self.setVisible(False)

    def _nameEdited(self, name: str):
        self._location.name = name
        self._save()
        self.locationNameChanged.emit(self._location)

    def _nameSet(self, _: str):
        emit_event(self._novel, RequestMilieuDictionaryResetEvent(self))

    def _summaryChanged(self):
        self._location.summary = self.textSummary.toPlainText()
        self._save()

    def _save(self):
        self.repo.update_novel(self._novel)
