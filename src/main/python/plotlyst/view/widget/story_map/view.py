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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QResizeEvent
from PyQt6.QtWidgets import QFrame, QApplication
from overrides import overrides
from qthandy import vbox, hbox, margins, sp, incr_icon

from src.main.python.plotlyst.core.domain import Character
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view.common import frame, shadow, tool_btn, ExclusiveOptionalButtonGroup, \
    TooltipPositionEventFilter
from src.main.python.plotlyst.view.icons import IconRegistry
from src.main.python.plotlyst.view.widget.characters import CharacterSelectorMenu
from src.main.python.plotlyst.view.widget.graphics import BaseGraphicsView
from src.main.python.plotlyst.view.widget.story_map.controls import EventSelectorWidget, StickerSelectorWidget
from src.main.python.plotlyst.view.widget.story_map.editors import StickerEditor, TextLineEditorPopup
from src.main.python.plotlyst.view.widget.story_map.items import EventItem, StickerItem, ItemType, MindMapNode, \
    CharacterItem
from src.main.python.plotlyst.view.widget.story_map.scene import EventsMindMapScene


class EventsMindMapView(BaseGraphicsView):

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel
        self._scene = EventsMindMapScene(self._novel)
        self.setScene(self._scene)
        self.setBackgroundBrush(QColor('#e9ecef'))

        self._controlsNavBar = self.__roundedFrame(self)
        sp(self._controlsNavBar).h_max()
        shadow(self._controlsNavBar)

        self._btnAddEvent = tool_btn(
            IconRegistry.from_name('mdi6.shape-square-rounded-plus'), 'Add new event', True,
            icon_resize=False, properties=['transparent-rounded-bg-on-hover', 'top-selector'],
            parent=self._controlsNavBar)
        self._btnAddCharacter = tool_btn(
            IconRegistry.character_icon('#040406'), 'Add new character', True,
            icon_resize=False, properties=['transparent-rounded-bg-on-hover', 'top-selector'],
            parent=self._controlsNavBar)
        self._btnAddSticker = tool_btn(IconRegistry.from_name('mdi6.sticker-circle-outline'), 'Add new sticker',
                                       True, icon_resize=False,
                                       properties=['transparent-rounded-bg-on-hover', 'top-selector'],
                                       parent=self._controlsNavBar)
        self._btnGroup = ExclusiveOptionalButtonGroup()
        self._btnGroup.addButton(self._btnAddEvent)
        self._btnGroup.addButton(self._btnAddCharacter)
        self._btnGroup.addButton(self._btnAddSticker)
        for btn in self._btnGroup.buttons():
            btn.installEventFilter(TooltipPositionEventFilter(btn))
            incr_icon(btn, 2)
        self._btnGroup.buttonClicked.connect(self._mainControlClicked)
        vbox(self._controlsNavBar, 5, 6)
        self._controlsNavBar.layout().addWidget(self._btnAddEvent)
        self._controlsNavBar.layout().addWidget(self._btnAddCharacter)
        self._controlsNavBar.layout().addWidget(self._btnAddSticker)

        self._wdgSecondaryEventSelector = EventSelectorWidget(self)
        self._wdgSecondaryEventSelector.setVisible(False)
        self._wdgSecondaryEventSelector.selected.connect(self._startAddition)
        self._wdgSecondaryStickerSelector = StickerSelectorWidget(self)
        self._wdgSecondaryStickerSelector.setVisible(False)
        self._wdgSecondaryStickerSelector.selected.connect(self._startAddition)

        self._stickerEditor = StickerEditor(self)
        self._stickerEditor.setVisible(False)

        self._wdgZoomBar = self.__roundedFrame(self)
        shadow(self._wdgZoomBar)
        hbox(self._wdgZoomBar, 2, spacing=6)
        margins(self._wdgZoomBar, left=10, right=10)

        self._btnZoomIn = tool_btn(IconRegistry.plus_circle_icon('lightgrey'), 'Zoom in', transparent_=True,
                                   parent=self._wdgZoomBar)
        self._btnZoomOut = tool_btn(IconRegistry.minus_icon('lightgrey'), 'Zoom out', transparent_=True,
                                    parent=self._wdgZoomBar)
        self._btnZoomIn.clicked.connect(lambda: self.scale(1.1, 1.1))
        self._btnZoomOut.clicked.connect(lambda: self.scale(0.9, 0.9))

        self._wdgZoomBar.layout().addWidget(self._btnZoomOut)
        self._wdgZoomBar.layout().addWidget(self._btnZoomIn)

        self._scene.itemAdded.connect(self._endAddition)
        self._scene.cancelItemAddition.connect(self._endAddition)
        self._scene.editEvent.connect(self._editEvent)
        self._scene.editSticker.connect(self._editSticker)
        self._scene.closeSticker.connect(self._hideSticker)

        self.__arrangeSideBars()

    @overrides
    def resizeEvent(self, event: QResizeEvent) -> None:
        super(EventsMindMapView, self).resizeEvent(event)
        self.__arrangeSideBars()

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

    def _mainControlClicked(self):
        self._wdgSecondaryEventSelector.setHidden(True)
        self._wdgSecondaryStickerSelector.setHidden(True)

        if self._btnAddEvent.isChecked():
            self._wdgSecondaryEventSelector.setVisible(True)
            self._startAddition(ItemType.EVENT)
        elif self._btnAddCharacter.isChecked():
            self._startAddition(ItemType.CHARACTER)
        elif self._btnAddSticker.isChecked():
            self._wdgSecondaryStickerSelector.setVisible(True)
            self._startAddition(ItemType.COMMENT)
        else:
            self._endAddition()

    def _startAddition(self, itemType: ItemType):
        self._scene.startAdditionMode(itemType)

        if not QApplication.overrideCursor():
            QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def _endAddition(self, itemType: Optional[ItemType] = None, item: Optional[MindMapNode] = None):
        btn = self._btnGroup.checkedButton()
        if btn:
            btn.setChecked(False)
        QApplication.restoreOverrideCursor()
        self._wdgSecondaryEventSelector.setHidden(True)
        self._wdgSecondaryStickerSelector.setHidden(True)
        self._scene.endAdditionMode()

        if itemType == ItemType.CHARACTER:
            self._endCharacterAddition(item)

    def _endCharacterAddition(self, item: CharacterItem):
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

    @staticmethod
    def __roundedFrame(parent=None) -> QFrame:
        frame_ = frame(parent)
        frame_.setProperty('relaxed-white-bg', True)
        frame_.setProperty('rounded', True)
        return frame_
