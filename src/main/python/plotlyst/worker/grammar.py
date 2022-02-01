"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from typing import Optional, Set

import language_tool_python
from PyQt5.QtCore import QRunnable
from language_tool_python import LanguageTool
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel, Event, Location
from src.main.python.plotlyst.event.core import emit_event, emit_critical, emit_info, EventListener
from src.main.python.plotlyst.event.handler import event_dispatcher
from src.main.python.plotlyst.events import LanguageToolSet, CharacterChangedEvent, LocationChangedEvent, ManuscriptLanguageChanged


class LanguageToolServerSetupWorker(QRunnable):

    @overrides
    def run(self) -> None:
        try:
            tool = language_tool_python.LanguageTool('en-US')
            tool.check('Test sentence.')
            language_tool_proxy.set(tool)
        except Exception as e:
            language_tool_proxy.set_error(str(e))


class LanguageToolProxy(EventListener):

    def __init__(self):
        self._language_tool: Optional[LanguageTool] = None
        self._error: Optional[str] = None
        event_dispatcher.register(self, ManuscriptLanguageChanged)

    @overrides
    def event_received(self, event: Event):
        if isinstance(event, ManuscriptLanguageChanged) and self.is_set():
            self._language_tool.language = event.lang

    def set(self, language_tool: LanguageTool):
        self._language_tool = language_tool
        self._error = None
        emit_info('Grammar checker was set up.')
        emit_event(LanguageToolSet(self, self._language_tool))

    def set_error(self, error_msg: str):
        self._error = error_msg
        emit_critical('Could not initialize LanguageTool grammar checker', self._error)

    def is_set(self) -> bool:
        return self._language_tool is not None

    def is_failed(self) -> bool:
        return self._error is not None

    @property
    def error(self) -> Optional[str]:
        return self._error

    @property
    def tool(self) -> LanguageTool:
        if self.is_set():
            return self._language_tool
        else:
            raise IOError('LanguageTool local server was not initialized yet')


language_tool_proxy = LanguageToolProxy()


class Dictionary(EventListener):
    def __init__(self):
        self.novel: Optional[Novel] = None
        self.words: Set[str] = set()
        event_dispatcher.register(self, CharacterChangedEvent)
        event_dispatcher.register(self, LocationChangedEvent)

    @overrides
    def event_received(self, event: Event):
        self.refresh()

    def set_novel(self, novel: Novel):
        self.novel = novel
        self.refresh()

    def refresh(self):
        self.words.clear()
        for character in self.novel.characters:
            self.words.add(character.name)
        for location in self.novel.locations:
            self._add_locations(location)

    def _add_locations(self, location: Location):
        self.words.add(location.name)
        for child in location.children:
            self._add_locations(child)

    def is_known_word(self, word: str) -> bool:
        return word in self.words


dictionary = Dictionary()
