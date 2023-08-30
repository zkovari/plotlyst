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

from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, RelationsNetwork, Character
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.character.network.scene import RelationsEditorScene, CharacterItem, \
    NetworkItemType, CharacterNetworkItemType
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorMenu
from src.main.python.plotlyst.view.widget.graphics import NodeItem, NetworkGraphicsView, NetworkScene


class CharacterNetworkView(NetworkGraphicsView):
    def __init__(self, novel: Novel, parent=None):
        self._novel = novel
        super(CharacterNetworkView, self).__init__(parent)

        self._btnAddCharacter = self._newControlButton(IconRegistry.character_icon('#040406'), 'Add new character',
                                                       CharacterNetworkItemType.CHARACTER)
        self._btnAddSticker = self._newControlButton(IconRegistry.from_name('mdi6.sticker-circle-outline'),
                                                     'Add new sticker', CharacterNetworkItemType.STICKER)

    @overrides
    def _initScene(self) -> NetworkScene:
        return RelationsEditorScene(self._novel)

    def relationsScene(self) -> RelationsEditorScene:
        return self._scene

    def refresh(self, network: RelationsNetwork):
        self._scene.clear()
        self._scene.setNetwork(network)
        for node in network.nodes:
            item = CharacterItem(node.character(self._novel), node)
            self._scene.addItem(item)
            item.setPos(node.x, node.y)

        self.centerOn(0, 0)

    @overrides
    def _startAddition(self, itemType: CharacterNetworkItemType):
        super()._startAddition(itemType)
        self._scene.startAdditionMode(itemType)

    @overrides
    def _endAddition(self, itemType: Optional[NetworkItemType] = None, item: Optional[NodeItem] = None):
        super()._endAddition(itemType, item)
        if itemType == CharacterNetworkItemType.CHARACTER:
            self._finishCharacterAddition(item)

    def _finishCharacterAddition(self, item: CharacterItem):
        def select(character: Character):
            item.setCharacter(character)

        popup = CharacterSelectorMenu(self._novel, parent=self)
        popup.selected.connect(select)
        view_pos = self.mapFromScene(item.sceneBoundingRect().topRight())
        popup.exec(self.mapToGlobal(view_pos))
