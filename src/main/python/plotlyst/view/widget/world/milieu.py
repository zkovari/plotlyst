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
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QLineEdit
from overrides import overrides
from qthandy import vbox, incr_font, sp, vspacer, line

from plotlyst.common import PLOTLYST_MAIN_COLOR
from plotlyst.core.domain import Novel, Location
from plotlyst.service.persistence import RepositoryPersistenceManager
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.tree import ContainerNode, TreeSettings, ItemBasedTreeView, ItemBasedNode


class LocationsParentNode(ContainerNode):
    newLocationRequested = pyqtSignal()

    def __init__(self, parent=None, settings: Optional[TreeSettings] = None):
        super().__init__('Locations', IconRegistry.location_icon(), parent, settings=settings)
        self.setMenuEnabled(False)
        self.setTranslucentIconEnabled(True)
        self.setSelectionEnabled(False)
        sp(self._lblTitle).h_min()
        self._btnAdd.setIcon(IconRegistry.plus_icon(PLOTLYST_MAIN_COLOR))
        self._btnAdd.clicked.connect(self.newLocationRequested.emit)


class LocationNode(ItemBasedNode):
    def __init__(self, location: Location, parent=None, settings: Optional[TreeSettings] = None):
        super().__init__(location.name, parent=parent, settings=settings)
        self._location = location
        self.setPlusButtonEnabled(False)
        self.setTranslucentIconEnabled(True)
        self._actionChangeIcon.setVisible(True)
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
    locationSelected = pyqtSignal(Location)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel: Optional[Novel] = None
        self._settings = TreeSettings(font_incr=2)

        self._nodeLocations = LocationsParentNode(settings=self._settings)
        self._nodeLocations.newLocationRequested.connect(self.addNewLocation)

        self._centralWidget.layout().addWidget(self._nodeLocations)
        self._centralWidget.layout().addWidget(vspacer())

        self.repo = RepositoryPersistenceManager.instance()

    def setNovel(self, novel: Novel):
        self._novel = novel

        self.clearSelection()
        self._nodes.clear()

        self._nodeLocations.clearChildren()
        for location in self._novel.locations:
            node = self.__initLocationNode(location)
            self._nodeLocations.addChild(node)

        if self._novel.locations:
            node = self._nodes[self._novel.locations[0]]
            node.select()
            self._selectionChanged(node, True)

    def addNewLocation(self):
        location = Location()
        node = self.__initLocationNode(location)
        self._nodeLocations.addChild(node)

        self._novel.locations.append(location)
        self._save()

    @overrides
    def _emitSelectionChanged(self, location: Location):
        self.locationSelected.emit(location)

    def _save(self):
        self.repo.update_novel(self._novel)

    def __initLocationNode(self, location: Location) -> LocationNode:
        node = LocationNode(location, settings=self._settings)
        self._nodes[location] = node
        node.selectionChanged.connect(partial(self._selectionChanged, node))
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

        vbox(self)
        self.layout().addWidget(self.lineEditName)
        self.layout().addWidget(line())

        self.repo = RepositoryPersistenceManager.instance()

        self.setVisible(False)

    def setLocation(self, location: Location):
        self.setVisible(True)
        self._location = location
        self.lineEditName.setText(self._location.name)
        if not self._location.name:
            self.lineEditName.setFocus()

    def _nameEdited(self, name: str):
        self._location.name = name
        self._save()
        self.locationNameChanged.emit(self._location)

    def _save(self):
        self.repo.update_novel(self._novel)
