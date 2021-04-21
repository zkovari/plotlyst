from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import dataclass_json

ACTION_SCENE = 'action'
REACTION_SCENE = 'reaction'


@dataclass_json
@dataclass
class Character:
    name: str
    personality: str = ''
    age: int = 0
    image_path: str = ''


@dataclass_json
@dataclass
class Scene:
    title: str
    synopsis: str = ''
    type: str = ''
    pivotal: bool = False
    event_1: str = ''
    event_2: str = ''
    event_3: str = ''
    pov: Optional[Character] = None
    characters: List[Character] = field(default_factory=list)
    wip: bool = False


@dataclass_json
@dataclass
class Novel:
    title: str
    config_path: str = ''
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
