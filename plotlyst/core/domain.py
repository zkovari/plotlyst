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
from dataclasses import dataclass, field
from typing import List, Optional, Any

ACTION_SCENE = 'action'
REACTION_SCENE = 'reaction'


@dataclass(unsafe_hash=True)
class Character:
    name: str
    id: Optional[int] = None
    avatar: Optional[Any] = None
    personality: str = ''
    age: int = 0


@dataclass(unsafe_hash=True)
class StoryLine:
    text: str
    id: Optional[int] = None


@dataclass
class Chapter:
    title: str
    sequence: int
    id: Optional[int] = None


@dataclass
class CharacterArc:
    arc: int
    character: Character


VERY_UNHAPPY: int = -2
UNHAPPY: int = -1
NEUTRAL: int = 0
HAPPY: int = 1
VERY_HAPPY: int = 2


@dataclass
class Scene:
    title: str
    id: Optional[int] = None
    synopsis: str = ''
    type: str = ''
    pivotal: str = ''
    sequence: int = 0
    beginning: str = ''
    middle: str = ''
    end: str = ''
    pov: Optional[Character] = None
    characters: List[Character] = field(default_factory=list)
    wip: bool = False
    story_lines: List[StoryLine] = field(default_factory=list)
    end_event: bool = True
    day: int = 0
    beginning_type: str = ''
    ending_hook: str = ''
    notes: str = ''
    chapter: Optional[Chapter] = None
    arcs: List[CharacterArc] = field(default_factory=list)


@dataclass
class Event:
    event: str
    day: int
    id: Optional[int] = None
    scene: Optional[Scene] = None
    character: Optional[Character] = None


@dataclass
class Novel:
    title: str
    id: Optional[int] = None
    config_path: str = ''
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
    story_lines: List[StoryLine] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    chapters: List[Chapter] = field(default_factory=list)


@dataclass
class Task:
    message: str
    reference: Optional[Any] = None
