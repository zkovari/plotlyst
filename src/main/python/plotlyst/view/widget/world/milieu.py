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
from typing import Optional, Set, Dict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QLineEdit
from overrides import overrides
from qthandy import vbox, incr_font, sp, vspacer

from plotlyst.common import PLOTLYST_MAIN_COLOR
from plotlyst.core.domain import Novel, Location
from plotlyst.view.icons import IconRegistry
from plotlyst.view.widget.tree import TreeView, ContainerNode, TreeSettings


class LocationsParentNode(ContainerNode):
    newLocationRequested = pyqtSignal()

    def __init__(self, parent=None, settings: Optional[TreeSettings] = None):
        super().__init__('Locations', IconRegistry.location_icon(), parent, settings=settings)
        self.setMenuEnabled(False)
        self.setTranslucentIconEnabled(True)
        sp(self._lblTitle).h_min()
        self._btnAdd.setIcon(IconRegistry.plus_icon(PLOTLYST_MAIN_COLOR))
        self._btnAdd.clicked.connect(self.newLocationRequested.emit)


class LocationNode(ContainerNode):
    def __init__(self, location: Location, parent=None, settings: Optional[TreeSettings] = None):
        super().__init__(location.name, parent=parent, settings=settings)
        self._location = location
        self.setPlusButtonEnabled(False)
        self.setTranslucentIconEnabled(True)
        self._actionChangeIcon.setVisible(True)
        self.refresh()

    def location(self) -> Location:
        return self._location

    def refresh(self):
        self._lblTitle.setText(self._location.name)
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


class LocationsTreeView(TreeView):
    locationSelected = pyqtSignal(Location)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._novel: Optional[Novel] = None
        self._settings = TreeSettings(font_incr=2)
        self._selectedLocations: Set[Location] = set()
        self._locations: Dict[Location, LocationNode] = {}

        self._nodeLocations = LocationsParentNode(settings=self._settings)
        self._nodeLocations.selectionChanged.connect(self._locationsParentSelectionChanged)
        self._nodeLocations.newLocationRequested.connect(self.addNewLocation)

        self._centralWidget.layout().addWidget(self._nodeLocations)
        self._centralWidget.layout().addWidget(vspacer())

    def setNovel(self, novel: Novel):
        self._novel = novel

        self.clearSelection()
        self._locations.clear()

        self._nodeLocations.clearChildren()
        for location in novel.locations:
            node = self.__initLocationNode(location)
            self._nodeLocations.addChild(node)

    def updateLocation(self, location: Location):
        self._locations[location].refresh()

    def clearSelection(self):
        for location in self._selectedLocations:
            self._locations[location].deselect()
        self._selectedLocations.clear()

    def addNewLocation(self):
        node = self.__initLocationNode(Location())
        self._nodeLocations.addChild(node)

    def _selectionChanged(self, node: LocationNode, selected: bool):
        if selected:
            self.clearSelection()
            self._nodeLocations.deselect()
            self._selectedLocations.add(node.location())
            self.locationSelected.emit(node.location())

    def _locationsParentSelectionChanged(self, selected: bool):
        if selected:
            self.clearSelection()

    def __initLocationNode(self, location: Location) -> LocationNode:
        node = LocationNode(location, settings=self._settings)
        self._locations[location] = node
        node.selectionChanged.connect(partial(self._selectionChanged, node))
        return node


class LocationEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._location: Optional[Location] = None

        self.lineEditName = QLineEdit()
        self.lineEditName.setPlaceholderText('Location name')
        self.lineEditName.setProperty('transparent', True)
        self.lineEditName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        incr_font(self.lineEditName, 8)

        vbox(self)
        self.layout().addWidget(self.lineEditName)

    def setLocation(self, location: Location):
        self._location = location
        self.lineEditName.setText(self._location.name)
