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
from dataclasses import dataclass

from src.main.python.plotlyst.core.domain import Character, Novel, NovelDescriptor
from src.main.python.plotlyst.event.core import Event


@dataclass
class NovelReloadRequestedEvent(Event):
    pass


@dataclass
class NovelReloadedEvent(Event):
    pass


@dataclass
class CharacterChangedEvent(Event):
    character: Character


@dataclass
class SceneChangedEvent(Event):
    pass


@dataclass
class SceneDeletedEvent(Event):
    pass


@dataclass
class NovelUpdatedEvent(Event):
    novel: NovelDescriptor


@dataclass
class NovelDeletedEvent(Event):
    novel: Novel


@dataclass
class StorylineCreatedEvent(Event):
    pass
