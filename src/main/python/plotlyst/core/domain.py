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
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any

ACTION_SCENE = 'action'
REACTION_SCENE = 'reaction'


@dataclass(unsafe_hash=True)
class Character:
    name: str
    id: Optional[uuid.UUID] = None
    avatar: Optional[Any] = None
    personality: str = ''
    age: int = 0


class NpcCharacter(Character):
    pass


@dataclass(unsafe_hash=True)
class StoryLine:
    text: str
    color_hexa: str = ''
    id: Optional[uuid.UUID] = None


@dataclass
class Chapter:
    title: str
    sequence: int
    id: Optional[uuid.UUID] = None


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
    id: Optional[uuid.UUID] = None
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
    day: int = 1
    beginning_type: str = ''
    ending_hook: str = ''
    notes: str = ''
    chapter: Optional[Chapter] = None
    arcs: List[CharacterArc] = field(default_factory=list)
    action_resolution: bool = False
    without_action_conflict: bool = False

    def pov_arc(self) -> int:
        for arc in self.arcs:
            if arc.character == self.pov:
                return arc.arc
        return NEUTRAL


@dataclass
class Novel:
    title: str
    id: Optional[uuid.UUID] = None
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
    story_lines: List[StoryLine] = field(default_factory=list)
    chapters: List[Chapter] = field(default_factory=list)

    def update_from(self, updated_novel: 'Novel'):
        self.title = updated_novel.title
        self.scenes.clear()
        self.scenes.extend(updated_novel.scenes)
        self.characters.clear()
        self.characters.extend(updated_novel.characters)
        self.chapters.clear()
        self.chapters.extend(updated_novel.chapters)
        self.story_lines.clear()
        self.story_lines.extend(updated_novel.story_lines)


class SceneBuilderElementType(Enum):
    SPEECH = 'speech'
    ACTION_BEAT = 'action_beat'
    CHARACTER_ENTRY = 'character_entry'
    REACTION = 'reaction'
    SIGHT = 'sight'
    SOUND = 'sound'
    SMELL = 'smell'
    TASTE = 'taste'
    TOUCH = 'touch'
    FEELING = 'feeling'
    REFLEX = 'reflex'
    ACTION = 'action'
    MONOLOG = 'monolog'
    EMOTIONAL_CHANGE = 'emotional_change'
    GOAL = 'goal'
    DISASTER = 'disaster'
    RESOLUTION = 'resolution'
    DECISION = 'decision'
    ENDING = 'ending'


@dataclass
class SceneBuilderElement:
    scene: Scene
    type: SceneBuilderElementType
    sequence: int
    text: str = ''
    children: List['SceneBuilderElement'] = field(default_factory=list)
    character: Optional[Character] = None
    id: Optional[int] = None
    has_suspense: bool = False
    has_tension: bool = False
    has_stakes: bool = False


@dataclass
class Task:
    message: str
    reference: Optional[Any] = None
