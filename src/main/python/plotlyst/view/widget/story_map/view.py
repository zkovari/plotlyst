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

import qtanim
from overrides import overrides

from src.main.python.plotlyst.core.domain import Character
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorMenu
from src.main.python.plotlyst.view.widget.graphics import NetworkGraphicsView, NetworkScene
from src.main.python.plotlyst.view.widget.story_map.controls import EventSelectorWidget, StickerSelectorWidget
from src.main.python.plotlyst.view.widget.story_map.editors import StickerEditor, TextLineEditorPopup, EventItemEditor
from src.main.python.plotlyst.view.widget.story_map.items import EventItem, StickerItem, ItemType, MindMapNode, \
    CharacterItem
from src.main.python.plotlyst.view.widget.story_map.scene import EventsMindMapScene


class EventsMindMapView(NetworkGraphicsView):

    def __init__(self, novel: Novel, parent=None):
        self._novel = novel
        super().__init__(parent)
        self._btnAddEvent = self._newControlButton(
            IconRegistry.from_name('mdi6.shape-square-rounded-plus'), 'Add new event', ItemType.EVENT)
        self._btnAddCharacter = self._newControlButton(
            IconRegistry.character_icon('#040406'), 'Add new character', ItemType.CHARACTER)
        self._btnAddSticker = self._newControlButton(IconRegistry.from_name('mdi6.sticker-circle-outline'),
                                                     'Add new sticker',
                                                     ItemType.COMMENT)

        self._wdgSecondaryEventSelector = EventSelectorWidget(self)
        self._wdgSecondaryEventSelector.setVisible(False)
        self._wdgSecondaryEventSelector.selected.connect(self._startAddition)
        self._wdgSecondaryStickerSelector = StickerSelectorWidget(self)
        self._wdgSecondaryStickerSelector.setVisible(False)
        self._wdgSecondaryStickerSelector.selected.connect(self._startAddition)

        self._stickerEditor = StickerEditor(self)
        self._stickerEditor.setVisible(False)

        self._itemEditor = EventItemEditor(self)
        self._itemEditor.setVisible(False)

        self._scene.editEvent.connect(self._editEvent)
        self._scene.editSticker.connect(self._editSticker)
        self._scene.closeSticker.connect(self._hideSticker)
        self._scene.showItemEditor.connect(self._showItemEditor)
        self._scene.hideItemEditor.connect(self._hideItemEditor)

        self._arrangeSideBars()

    @overrides
    def _initScene(self) -> NetworkScene:
        return EventsMindMapScene(self._novel)

    def _editEvent(self, item: EventItem):
        def setText(text: str):
            item.setText(text)

        popup = TextLineEditorPopup(item.text(), item.textRect(), parent=self)
        view_pos = self.mapFromScene(item.textSceneRect().topLeft())
        popup.exec(self.mapToGlobal(view_pos))

        popup.aboutToHide.connect(lambda: setText(popup.text()))

    def _editSticker(self, sticker: StickerItem):
        view_pos = self.mapFromScene(sticker.sceneBoundingRect().topRight())
        self._stickerEditor.move(view_pos)
        qtanim.fade_in(self._stickerEditor)

    def _hideSticker(self):
        if not self._stickerEditor.underMouse():
            self._stickerEditor.setHidden(True)

    def _showItemEditor(self, item: MindMapNode):
        self._itemEditor.setItem(item)

        item_w = item.sceneBoundingRect().width()
        editor_w = self._itemEditor.sizeHint().width()
        diff_w = int(editor_w - item_w) // 2

        view_pos = self.mapFromScene(item.sceneBoundingRect().topLeft())
        view_pos.setX(view_pos.x() - diff_w)
        view_pos.setY(view_pos.y() - 50)
        self._itemEditor.move(view_pos)
        self._itemEditor.setVisible(True)

    def _hideItemEditor(self):
        self._itemEditor.setVisible(False)

    @overrides
    def _startAddition(self, itemType: ItemType):
        super()._startAddition(itemType)
        self._wdgSecondaryEventSelector.setHidden(True)
        self._wdgSecondaryStickerSelector.setHidden(True)
        self._hideItemEditor()

        if itemType == ItemType.EVENT:
            self._wdgSecondaryEventSelector.setVisible(True)
        elif itemType == ItemType.COMMENT:
            self._wdgSecondaryStickerSelector.setVisible(True)

    @overrides
    def _endAddition(self, itemType: Optional[ItemType] = None, item: Optional[MindMapNode] = None):
        super()._endAddition(itemType, item)
        self._wdgSecondaryEventSelector.setHidden(True)
        self._wdgSecondaryStickerSelector.setHidden(True)

        if itemType == ItemType.CHARACTER:
            self._endCharacterAddition(item)

    def _endCharacterAddition(self, item: CharacterItem):
        def select(character: Character):
            item.setCharacter(character)

        popup = CharacterSelectorMenu(self._novel, parent=self)
        popup.selected.connect(select)
        view_pos = self.mapFromScene(item.sceneBoundingRect().topRight())
        popup.exec(self.mapToGlobal(view_pos))

    def _arrangeSideBars(self):
        super()._arrangeSideBars()

        secondary_x = self._controlsNavBar.pos().x() + self._controlsNavBar.sizeHint().width() + 5
        secondary_y = self._controlsNavBar.pos().y() + self._btnAddEvent.pos().y()
        self._wdgSecondaryEventSelector.setGeometry(secondary_x, secondary_y,
                                                    self._wdgSecondaryEventSelector.sizeHint().width(),
                                                    self._wdgSecondaryEventSelector.sizeHint().height())

        secondary_x = self._controlsNavBar.pos().x() + self._controlsNavBar.sizeHint().width() + 5
        secondary_y = self._controlsNavBar.pos().y() + self._btnAddSticker.pos().y()
        self._wdgSecondaryStickerSelector.setGeometry(secondary_x, secondary_y,
                                                      self._wdgSecondaryStickerSelector.sizeHint().width(),
                                                      self._wdgSecondaryStickerSelector.sizeHint().height())
