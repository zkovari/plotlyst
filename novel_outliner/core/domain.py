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
