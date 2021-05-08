from dataclasses import dataclass, field
from typing import List, Optional

ACTION_SCENE = 'action'
REACTION_SCENE = 'reaction'


@dataclass(unsafe_hash=True)
class Character:
    name: str
    id: Optional[int] = None
    personality: str = ''
    age: int = 0


@dataclass(unsafe_hash=True)
class StoryLine:
    text: str
    id: Optional[int] = None


@dataclass
class Scene:
    title: str
    id: Optional[int] = None
    synopsis: str = ''
    type: str = ''
    pivotal: bool = False
    sequence: int = 0
    beginning: str = ''
    middle: str = ''
    end: str = ''
    pov: Optional[Character] = None
    characters: List[Character] = field(default_factory=list)
    wip: bool = False
    story_lines: List[StoryLine] = field(default_factory=list)


@dataclass
class Novel:
    title: str
    id: Optional[int] = None
    config_path: str = ''
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
    story_lines: List[StoryLine] = field(default_factory=list)
