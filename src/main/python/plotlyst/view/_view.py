"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.event.core import EventListener, Event
from src.main.python.plotlyst.model.events import NovelReloadedEvent


class AbstractView(QObject, EventListener):

    def __init__(self):
        super().__init__(None)
        self._refresh_on_activation: bool = False
        self.widget = QWidget()

    @overrides
    def event_received(self, event: Event):
        pass

    def activate(self):
        if self._refresh_on_activation:
            self.refresh()
            self._refresh_on_activation = False

    @abstractmethod
    def refresh(self):
        pass


class AbstractNovelView(AbstractView):

    def __init__(self, novel: Novel):
        super().__init__()
        self.novel = novel

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, NovelReloadedEvent):
            if self.widget.isVisible():
                self.refresh()
            else:
                self._refresh_on_activation = True

    @abstractmethod
    def refresh(self):
        pass
