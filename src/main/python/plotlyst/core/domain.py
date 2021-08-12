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

from src.main.python.plotlyst.common import PIVOTAL_COLOR

ACTION_SCENE = 'action'
REACTION_SCENE = 'reaction'


@dataclass(unsafe_hash=True)
class Character:
    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    avatar: Optional[Any] = None
    personality: str = ''
    age: int = 0


class NpcCharacter(Character):
    pass


@dataclass(unsafe_hash=True)
class StoryLine:
    text: str
    color_hexa: str = ''
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Chapter:
    title: str
    sequence: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class CharacterArc:
    arc: int
    character: Character


VERY_UNHAPPY: int = -2
UNHAPPY: int = -1
NEUTRAL: int = 0
HAPPY: int = 1
VERY_HAPPY: int = 2


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
    type: SceneBuilderElementType
    text: str = ''
    children: List['SceneBuilderElement'] = field(default_factory=list)
    character: Optional[Character] = None
    has_suspense: bool = False
    has_tension: bool = False
    has_stakes: bool = False


@dataclass
class SceneStage:
    stage: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class StoryBeat:
    text: str
    act: int
    ends_act: bool = False
    color_hexa: str = PIVOTAL_COLOR
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Scene:
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    synopsis: str = ''
    type: str = ''
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
    builder_elements: List[SceneBuilderElement] = field(default_factory=list)
    stage: Optional[SceneStage] = None
    beat: Optional[StoryBeat] = None

    def pov_arc(self) -> int:
        for arc in self.arcs:
            if arc.character == self.pov:
                return arc.arc
        return NEUTRAL


def default_stages() -> List[SceneStage]:
    return [SceneStage('Outlined'), SceneStage('1st Draft'),
            SceneStage('2nd Draft'), SceneStage('3rd Draft'), SceneStage('4th Draft'),
            SceneStage('Edited'), SceneStage('Proofread'), SceneStage('Final')]


@dataclass
class StoryStructure:
    title: str
    icon: str = ''
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    beats: List[StoryBeat] = field(default_factory=list)
    custom: bool = False


default_story_structures = [StoryStructure(title='Three Act Structure',
                                           id=uuid.UUID('58013be5-1efb-4de4-9dd2-1433ce6edf90'),
                                           icon='mdi.numeric-3-circle-outline',
                                           beats=[StoryBeat(text='Exposition',
                                                            id=uuid.UUID('40365047-e7df-4543-8816-f9f8dcce12da'),
                                                            act=1),
                                                  StoryBeat(text='Inciting Incident',
                                                            id=uuid.UUID('a0c2d94a-b53c-485e-a279-f2548bdb38ec'),
                                                            act=1),
                                                  StoryBeat(text='Plot Point One',
                                                            id=uuid.UUID('8d85c960-1c63-44d4-812d-545d3ba4d153'), act=1,
                                                            ends_act=True),
                                                  StoryBeat(text='Rising Action',
                                                            id=uuid.UUID('991354ea-2e8e-46f2-bd42-11fa56f73801'),
                                                            act=2),
                                                  StoryBeat(text='Midpoint',
                                                            id=uuid.UUID('3f817e10-85d1-46af-91c6-70f1ad5c0542'),
                                                            act=2),
                                                  StoryBeat(text='Plot Point Two',
                                                            id=uuid.UUID('4ded5006-c90a-4825-9de7-e16bf62017a3'), act=2,
                                                            ends_act=True),
                                                  StoryBeat(text='Pre Climax',
                                                            id=uuid.UUID('17a85b2a-76fb-44ec-a367-bccf6cd5f8aa'),
                                                            act=3),
                                                  StoryBeat(text='Climax',
                                                            id=uuid.UUID('342eb27c-52ff-40c2-8c5e-cf563d4e38bc'),
                                                            act=3),
                                                  StoryBeat(text='Denouement',
                                                            id=uuid.UUID('996695b1-8db6-4c68-8dc4-51bbfe720e8b'),
                                                            act=3),
                                                  ]),
                            StoryStructure(title='Save the Cat',
                                           id=uuid.UUID('1f1c4433-6afa-48e1-a8dc-f8fcb94bfede'),
                                           icon='fa5s.cat',
                                           beats=[StoryBeat(text='Opening Image',
                                                            id=uuid.UUID('249bba52-98b8-4577-8b3c-94481f6bf622'),
                                                            act=1),
                                                  StoryBeat(text='Set-up',
                                                            id=uuid.UUID('7ce4345b-60eb-4cd6-98cc-7cce98028839'),
                                                            act=1),
                                                  StoryBeat(text='Theme Stated',
                                                            id=uuid.UUID('1c8b0903-f169-48d5-bcec-3e842f360150'),
                                                            act=1),
                                                  StoryBeat(text='Catalyst',
                                                            id=uuid.UUID('cc3d8641-bcdf-402b-ba84-7ff59b2cc76a'),
                                                            act=1),
                                                  StoryBeat(text='Debate',
                                                            id=uuid.UUID('0203696e-dc54-4a10-820a-bfdf392a82dc'),
                                                            act=1),
                                                  StoryBeat(text='Break into Two',
                                                            id=uuid.UUID('43eb267f-2840-437b-9eac-9e52d80eba2b'),
                                                            act=1, ends_act=True),
                                                  StoryBeat(text='B Story',
                                                            id=uuid.UUID('64229c74-5513-4391-9b45-c54ad106c137'),
                                                            act=2),
                                                  StoryBeat(text='Fun and Games',
                                                            id=uuid.UUID('490157f0-f255-4ab3-82f3-bc5cb22ce03b'),
                                                            act=2),
                                                  StoryBeat(text='Midpoint',
                                                            id=uuid.UUID('af4fb4e9-f287-47b6-b219-be75af752622'),
                                                            act=2),
                                                  StoryBeat(text='Bad Guys Close In',
                                                            id=uuid.UUID('2060c95f-dcdb-4074-a096-4b054f70d57a'),
                                                            act=2),
                                                  StoryBeat(text='All is Lost',
                                                            id=uuid.UUID('2971ce1a-eb69-4ac1-9f2d-74407e6fac92'),
                                                            act=2),
                                                  StoryBeat(text='Dark Night of the Soul',
                                                            id=uuid.UUID('c0e89a87-224d-4b97-b4f5-a2ace08fdadb'),
                                                            act=2),
                                                  StoryBeat(text='Break into Three',
                                                            id=uuid.UUID('677f83ad-355a-47fb-8ff7-812997bdb23a'),
                                                            act=2, ends_act=True),
                                                  StoryBeat(text='Gather the Team',
                                                            id=uuid.UUID('777d81b6-b427-4fc0-ba8d-01cde45eedde'),
                                                            act=3),
                                                  StoryBeat(text='Execute the Plan',
                                                            id=uuid.UUID('b99012a6-8c41-43c8-845d-7595ce7140d9'),
                                                            act=3),
                                                  StoryBeat(text='High Tower Surprise',
                                                            id=uuid.UUID('fe77f4f2-9064-4b06-8062-920635aa415c'),
                                                            act=3),
                                                  StoryBeat(text='Dig Deep Down',
                                                            id=uuid.UUID('a5c4d0aa-9811-4988-8611-3483b2499732'),
                                                            act=3),
                                                  StoryBeat(text='Execute a New Plan',
                                                            id=uuid.UUID('13d535f6-6b3d-4211-ae44-e0fcf3970186'),
                                                            act=3),
                                                  StoryBeat(text='Final Image',
                                                            id=uuid.UUID('12d5ec21-af96-4e51-9c26-06583d830d87'),
                                                            act=3),
                                                  ])]


@dataclass
class NovelDescriptor:
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Novel:
    title: str
    story_structure: StoryStructure = default_story_structures[0]
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
    story_lines: List[StoryLine] = field(default_factory=list)
    chapters: List[Chapter] = field(default_factory=list)
    stages: List[SceneStage] = field(default_factory=default_stages)

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


@dataclass
class Task:
    message: str
    reference: Optional[Any] = None
