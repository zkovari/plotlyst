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

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent
from overrides import overrides

from src.main.python.plotlyst.core.client import json_client
from src.main.python.plotlyst.core.domain import Novel, Node, Character
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager
from src.main.python.plotlyst.view.widget.graphics import NetworkScene, AbstractSocketItem, EventItem
from src.main.python.plotlyst.view.widget.story_map.items import MindMapNode, StickerItem


class EventsMindMapScene(NetworkScene):
    editSticker = pyqtSignal(StickerItem)
    closeSticker = pyqtSignal()
    showItemEditor = pyqtSignal(MindMapNode)
    hideItemEditor = pyqtSignal()

    def __init__(self, novel: Novel, parent=None):
        super().__init__(parent)
        self._novel = novel

        self.repo = RepositoryPersistenceManager.instance()

    @overrides
    def startLink(self, source: AbstractSocketItem):
        super().startLink(source)
        self.hideEditor()

    def editEventText(self, item: EventItem):
        self.editEvent.emit(item)

    def showEditor(self, item: MindMapNode):
        if not self._selectionMode:
            self.showItemEditor.emit(item)

    def hideEditor(self):
        if len(self.selectedItems()) == 1:
            self.hideItemEditor.emit()

    @overrides
    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        if not event.modifiers() and not event.key() == Qt.Key.Key_Escape and len(self.selectedItems()) == 1:
            item = self.selectedItems()[0]
            if isinstance(item, EventItem):
                self.editEvent.emit(item)

    def displayStickerMessage(self, sticker: StickerItem):
        self.editSticker.emit(sticker)

    def hideStickerMessage(self):
        self.closeSticker.emit()

    @overrides
    def _character(self, node: Node) -> Optional[Character]:
        return node.character(self._novel) if node.character_id else None

    @overrides
    def _load(self):
        json_client.load_diagram(self._novel, self._diagram)

    @overrides
    def _save(self):
        self.repo.update_diagram(self._novel, self._diagram)
