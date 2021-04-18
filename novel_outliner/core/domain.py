from dataclasses import dataclass, field
from typing import List

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Character:
    name: str
    personality: str = ''
    age: int = 0


@dataclass_json
@dataclass
class Novel:
    title: str
    config_path: str = ''
    characters: List[Character] = field(default_factory=list)
