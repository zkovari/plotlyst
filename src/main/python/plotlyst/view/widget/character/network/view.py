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

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QResizeEvent, QColor
from PyQt6.QtWidgets import QFrame, QApplication
from overrides import overrides
from qthandy import sp, incr_icon, vbox

from src.main.python.plotlyst.core.domain import Novel, RelationsNetwork, Character
from src.main.python.plotlyst.view.common import shadow, tool_btn, ExclusiveOptionalButtonGroup, \
    TooltipPositionEventFilter, frame
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.character.network.scene import RelationsEditorScene, CharacterItem, \
    NetworkItemType
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorMenu
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView, ZoomBar, NodeItem


class CharacterNetworkView(BaseGraphicsView):
    def __init__(self, novel: Novel, parent=None):
        super(CharacterNetworkView, self).__init__(parent)
        self._novel = novel
        self._scene = RelationsEditorScene(self._novel)
        self.setScene(self._scene)
        self.setBackgroundBrush(QColor('#e9ecef'))

        # self._linkEditorMenu = QMenu(self)
        # self._linkEditorMenu.addAction('Friendship')
        # self._linkEditorMenu.addAction('Colleagues')
        # self._linkEditorMenu.addAction('Love')

        self._wdgZoomBar = ZoomBar(self)
        self._wdgZoomBar.zoomed.connect(lambda x: self.scale(1.0 + x, 1.0 + x))

        self._controlsNavBar = self.__roundedFrame(self)
        sp(self._controlsNavBar).h_max()
        shadow(self._controlsNavBar)

        self._btnAddCharacter = tool_btn(
            IconRegistry.character_icon('#040406'), 'Add new character', True,
            icon_resize=False, properties=['transparent-rounded-bg-on-hover', 'top-selector'],
            parent=self._controlsNavBar)
        self._btnAddSticker = tool_btn(IconRegistry.from_name('mdi6.sticker-circle-outline'), 'Add new sticker',
                                       True, icon_resize=False,
                                       properties=['transparent-rounded-bg-on-hover', 'top-selector'],
                                       parent=self._controlsNavBar)

        self._btnGroup = ExclusiveOptionalButtonGroup()
        self._btnGroup.addButton(self._btnAddCharacter)
        self._btnGroup.addButton(self._btnAddSticker)

        for btn in self._btnGroup.buttons():
            btn.installEventFilter(TooltipPositionEventFilter(btn))
            incr_icon(btn, 2)
        self._btnGroup.buttonClicked.connect(self._mainControlClicked)
        vbox(self._controlsNavBar, 5, 6)
        self._controlsNavBar.layout().addWidget(self._btnAddCharacter)
        self._controlsNavBar.layout().addWidget(self._btnAddSticker)

        self._scene.itemAdded.connect(self._endAddition)
        self._scene.cancelItemAddition.connect(self._endAddition)
        self._scene.charactersLinked.connect(self._charactersLinked)

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
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.__arrangeSideBars()

    def _charactersLinked(self, item: CharacterItem):
        view_pos = self.mapFromScene(item.sceneBoundingRect().topRight())
        self._linkEditorMenu.popup(self.mapToGlobal(view_pos))

    def _mainControlClicked(self):
        # self._wdgSecondaryEventSelector.setHidden(True)
        # self._wdgSecondaryStickerSelector.setHidden(True)

        if self._btnAddCharacter.isChecked():
            self._startAddition(NetworkItemType.CHARACTER)
        # elif self._btnAddSticker.isChecked():
        #     self._wdgSecondaryStickerSelector.setVisible(True)
        #     self._startAddition(ItemType.COMMENT)
        # else:
        #     self._endAddition()

    def _startAddition(self, itemType: NetworkItemType):
        self._scene.startAdditionMode(itemType)
        for btn in self._btnGroup.buttons():
            if not btn.isChecked():
                btn.setDisabled(True)

        if not QApplication.overrideCursor():
            QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def _endAddition(self, itemType: Optional[NetworkItemType] = None, item: Optional[NodeItem] = None):
        for btn in self._btnGroup.buttons():
            btn.setEnabled(True)
            if btn.isChecked():
                btn.setChecked(False)
        QApplication.restoreOverrideCursor()

        if itemType == NetworkItemType.CHARACTER:
            self._finishCharacterAddition(item)

    def _finishCharacterAddition(self, item: CharacterItem):
        def select(character: Character):
            item.setCharacter(character)

        popup = CharacterSelectorMenu(self._novel, parent=self)
        popup.selected.connect(select)
        view_pos = self.mapFromScene(item.sceneBoundingRect().topRight())
        popup.exec(self.mapToGlobal(view_pos))

    def __arrangeSideBars(self):
        self._wdgZoomBar.setGeometry(10, self.height() - self._wdgZoomBar.sizeHint().height() - 10,
                                     self._wdgZoomBar.sizeHint().width(),
                                     self._wdgZoomBar.sizeHint().height())
        self._controlsNavBar.setGeometry(10, 100, self._controlsNavBar.sizeHint().width(),
                                         self._controlsNavBar.sizeHint().height())

    @staticmethod
    def __roundedFrame(parent=None) -> QFrame:
        frame_ = frame(parent)
        frame_.setProperty('relaxed-white-bg', True)
        frame_.setProperty('rounded', True)
        return frame_
