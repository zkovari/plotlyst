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
from abc import abstractmethod
from typing import List, Any, Optional

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QWidget, QButtonGroup
from overrides import overrides
from qthandy import busy
from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.event.handler import global_event_dispatcher, event_dispatchers
from src.main.python.plotlyst.events import CharacterDeletedEvent, NovelSyncEvent
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager


class AbstractView(QObject, EventListener):

    def __init__(self, event_types: Optional[List[Any]] = None):
        super().__init__(None)
        self._refresh_on_activation: bool = False
        self.widget = QWidget()
        self.title: Optional[QWidget] = None
        self._navigable_button_group: Optional[QButtonGroup] = None
        if event_types:
            self._event_types = event_types
        else:
            self._event_types = []

        for event in self._event_types:
            global_event_dispatcher.register(self, event)

        self.repo = RepositoryPersistenceManager.instance()

    def setNavigableButtonGroup(self, group: QButtonGroup):
        self._navigable_button_group = group
        for i, btn in enumerate(self._navigable_button_group.buttons()):
            self._navigable_button_group.setId(btn, i)

    @overrides
    def event_received(self, event: Event):
        refresh = False
        for et in self._event_types:
            if isinstance(event, et):
                refresh = True
        if refresh:
            if self.widget.isVisible():
                self.refresh()
            else:
                self._refresh_on_activation = True

    def activate(self):
        if self._refresh_on_activation:
            self.refresh()
            self._refresh_on_activation = False

    @abstractmethod
    def refresh(self):
        pass

    def jumpToPrevious(self):
        if self._navigable_button_group is None:
            return

        id_ = self._navigable_button_group.checkedId()
        if id_ == 0:
            id_ = len(self._navigable_button_group.buttons()) - 1
        else:
            id_ -= 1
        self._navigable_button_group.button(id_).setChecked(True)

    def jumpToNext(self):
        if self._navigable_button_group is None:
            return

        id_ = self._navigable_button_group.checkedId()
        if id_ == len(self._navigable_button_group.buttons()) - 1:
            id_ = 0
        else:
            id_ += 1
        self._navigable_button_group.button(id_).setChecked(True)


class AbstractNovelView(AbstractView):

    def __init__(self, novel: Novel, event_types: Optional[List[Any]] = None):
        events = event_types if event_types else []

        if CharacterDeletedEvent not in events:
            events.append(CharacterDeletedEvent)
        if NovelSyncEvent not in events:
            events.append(NovelSyncEvent)
        super().__init__()

        self.novel = novel
        self._dispatcher = event_dispatchers.instance(self.novel)
        self._dispatcher.register(self, events)

    @busy
    @abstractmethod
    def refresh(self):
        pass
