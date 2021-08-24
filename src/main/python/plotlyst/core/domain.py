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
from typing import List, Optional, Any, Dict

from PyQt5.QtCore import Qt

from src.main.python.plotlyst.common import PIVOTAL_COLOR

ACTION_SCENE = 'action'
REACTION_SCENE = 'reaction'


@dataclass
class TemplateValue:
    id: uuid.UUID
    value: Any


@dataclass
class Event:
    keyphrase: str
    synopsis: str
    conflicts: List['Conflict'] = field(default_factory=list)
    emotion: int = 0


@dataclass
class BackstoryEvent(Event):
    age: int = 0
    as_baby: bool = False
    as_child: bool = False
    as_teenager: bool = False
    as_adult: bool = False


@dataclass
class Character:
    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    avatar: Optional[Any] = None
    template_values: List[TemplateValue] = field(default_factory=list)
    backstory: List[BackstoryEvent] = field(default_factory=list)

    def enneagram(self) -> Optional['SelectionItem']:
        for value in self.template_values:
            if value.id == enneagram_field.id:
                return _enneagram_choices.get(value.value)

    def role(self) -> Optional['SelectionItem']:
        for value in self.template_values:
            if value.id == role_field.id:
                item = _role_choices.get(value.value)
                if not item:
                    return None
                if item.text == 'Protagonist' and self.gender() == 1:
                    return SelectionItem(item.text, item.type, 'fa5s.chess-queen', item.icon_color)
                return item

    def gender(self) -> int:
        for value in self.template_values:
            if value.id == gender_field.id:
                return value.value[0] if value.value else -1
        return -1


class NpcCharacter(Character):
    pass


@dataclass(unsafe_hash=True)
class DramaticQuestion:
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


class ConflictType(Enum):
    CHARACTER = 0
    SOCIETY = 1
    NATURE = 2
    TECHNOLOGY = 3
    SUPERNATURAL = 4
    SELF = 5


@dataclass
class Conflict:
    keyphrase: str
    type: ConflictType
    pov: Character
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    character: Optional[Character] = None


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
    dramatic_questions: List[DramaticQuestion] = field(default_factory=list)
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
    conflicts: List[Conflict] = field(default_factory=list)

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


class TemplateFieldType(Enum):
    TEXT = 0
    SMALL_TEXT = 1
    TEXT_SELECTION = 2
    BUTTON_SELECTION = 3
    NUMERIC = 4
    IMAGE = 5
    LABELS = 6


class SelectionType(Enum):
    SINGLE_LIST = 0
    CHECKBOX = 1
    CHECKED_BUTTON = 2
    TAGS = 3


class SelectionItemType(Enum):
    CHOICE = 0
    SEPARATOR = 1


@dataclass
class SelectionItem:
    text: str
    type: SelectionItemType = SelectionItemType.CHOICE
    icon: str = ''
    icon_color: str = 'black'
    meta: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.text)


@dataclass
class TemplateField:
    name: str
    type: TemplateFieldType
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    description: str = ''
    emoji: str = ''
    placeholder: str = ''
    selections: List[SelectionItem] = field(default_factory=list)
    highlighted: bool = False
    required: bool = False
    exclusive: bool = False
    custom: bool = False
    min_value: int = 0
    max_value = 2_147_483_647
    compact: bool = False
    frozen: bool = False
    show_label: bool = True


name_field = TemplateField(name='Name', type=TemplateFieldType.TEXT, emoji=':bust_in_silhouette:', placeholder='Name',
                           id=uuid.UUID('45525d2e-3ba7-40e4-b072-e367f96a6eb4'), required=True, highlighted=True,
                           frozen=True, compact=True, show_label=False)
avatar_field = TemplateField(name='Avatar', type=TemplateFieldType.IMAGE,
                             id=uuid.UUID('c3b5c7b5-6fd2-4ae1-959d-6fabd659cb3c'), required=True, highlighted=True,
                             frozen=True, compact=True, show_label=False)
age_field = TemplateField(name='Age', type=TemplateFieldType.NUMERIC,
                          id=uuid.UUID('7c8fccb8-9228-495a-8edd-3f991ebeed4b'), compact=True)
gender_field = TemplateField(name='Gender', type=TemplateFieldType.BUTTON_SELECTION,
                             id=uuid.UUID('dd5421f5-b332-4295-8020-e69c482a2ac5'),
                             selections=[SelectionItem('Male', icon='mdi.gender-male', icon_color='#067bc2'),
                                         SelectionItem('Female', icon='mdi.gender-female', icon_color='#832161')],
                             compact=True, exclusive=True)
enneagram_field = TemplateField(name='Enneagram', type=TemplateFieldType.TEXT_SELECTION,
                                id=uuid.UUID('be281490-c1b7-413c-b519-f780dbdafaeb'),
                                selections=[SelectionItem('Perfectionist', icon='mdi.numeric-1-circle',
                                                          icon_color='#1f487e',
                                                          meta={'positive': ['Rational', 'Principled', 'Objective',
                                                                             'Structured'],
                                                                'negative': ['Strict'],
                                                                'desire': 'Being good, balanced, have integrity',
                                                                'fear': 'Being incorrect, corrupt, evil'}),
                                            SelectionItem('Giver', icon='mdi.numeric-2-circle',
                                                          icon_color='#7ae7c7',
                                                          meta={'positive': ['Generous', 'Warm', 'Caring'],
                                                                'negative': ['Possessive'],
                                                                'desire': 'To be loved and appreciated',
                                                                'fear': 'Being unloved, unwanted'}
                                                          ),
                                            SelectionItem('Achiever', icon='mdi.numeric-3-circle',
                                                          icon_color='#297045',
                                                          meta={'positive': ['Pragmatic', 'Driven', 'Ambitious'],
                                                                'negative': ['Image-conscious'],
                                                                'desire': 'Be valuable and worthwhile',
                                                                'fear': 'Being worthless'}
                                                          ),
                                            SelectionItem('Individualist', icon='mdi.numeric-4-circle',
                                                          icon_color='#4d8b31',
                                                          meta={'positive': ['Self-aware', 'Sensitive', 'Expressive'],
                                                                'negative': ['Temperamental'],
                                                                'desire': 'Express their individuality',
                                                                'fear': 'Having no identity or significance'}
                                                          ),
                                            SelectionItem('Investigator', icon='mdi.numeric-5-circle',
                                                          icon_color='#ffc600',
                                                          meta={'positive': ['Perceptive', 'Curious', 'Innovative'],
                                                                'negative': ['Isolated'],
                                                                'desire': 'Be competent',
                                                                'fear': 'Being useless, incompetent'}
                                                          ),
                                            SelectionItem('Skeptic', icon='mdi.numeric-6-circle',
                                                          icon_color='#ff6b35',
                                                          meta={'positive': ['Committed', 'Responsible', 'Organized'],
                                                                'negative': ['Anxious'],
                                                                'desire': 'Have security and support',
                                                                'fear': 'Being vulnerable and unprepared'}
                                                          ),
                                            SelectionItem('Enthusiast', icon='mdi.numeric-7-circle',
                                                          icon_color='#ec0b43',
                                                          meta={'positive': ['Optimistic', 'Flexible', 'Practical',
                                                                             'Adventurous'],
                                                                'negative': ['Impulsive', 'Self-centered'],
                                                                'desire': 'Be stimulated, engaged, satisfied',
                                                                'fear': 'Being deprived'}
                                                          ),
                                            SelectionItem('Challenger', icon='mdi.numeric-8-circle',
                                                          icon_color='#4f0147',
                                                          meta={'positive': ['Decisive', 'Powerful', 'Assertive',
                                                                             'Independent'],
                                                                'negative': ['Confrontational'],
                                                                'desire': 'Be independent and in control',
                                                                'fear': 'Being vulnerable, controlled, harmed'}
                                                          ),
                                            SelectionItem('Peacemaker', icon='mdi.numeric-9-circle',
                                                          icon_color='#3a015c',
                                                          meta={'positive': ['Easygoing', 'Understanding', 'Patient',
                                                                             'Supportive'],
                                                                'negative': ['Lazy', 'Indecisive'],
                                                                'desire': 'Internal peace, harmony',
                                                                'fear': 'Loss, separation'}
                                                          )],
                                compact=True)
mbti_field = TemplateField(name='MBTI', type=TemplateFieldType.TEXT_SELECTION,
                           id=uuid.UUID('bc5408a4-c2bd-4370-b46b-95f20018af01'),
                           selections=[SelectionItem('INTJ'),
                                       SelectionItem('INTP'),
                                       SelectionItem('ENTJ'),
                                       SelectionItem('ENTP'),
                                       SelectionItem('INFJ'),
                                       SelectionItem('INFP'),
                                       SelectionItem('ENFJ'),
                                       SelectionItem('ENFP'),
                                       SelectionItem('ISTJ'),
                                       SelectionItem('ISFJ'),
                                       SelectionItem('ESTJ'),
                                       SelectionItem('ESFJ'),
                                       SelectionItem('ISTP'),
                                       SelectionItem('ISFP'),
                                       SelectionItem('ESTP'),
                                       SelectionItem('ESFP'), ], compact=True)

positive_traits = sorted(['Generous', 'Objective', 'Principled', 'Rational',
                          'Structured', 'Caring', 'Warm', 'Driven', 'Ambitious', 'Self-aware', 'Sensitive',
                          'Expressive', 'Perceptive', 'Curious', 'Innovative', 'Committed', 'Responsible', 'Organized',
                          'Optimistic', 'Flexible', 'Practical',
                          'Adventurous', 'Decisive', 'Powerful', 'Assertive',
                          'Independent', 'Easygoing', 'Understanding', 'Patient',
                          'Supportive'])
negative_traits = sorted(
    ['Anxious', 'Confrontational', 'Indecisive', 'Strict', 'Possessive', 'Image-conscious', 'Temperamental',
     'Isolated', 'Impulsive', 'Self-centered', 'Lazy'])

traits_field = TemplateField(name='Traits', type=TemplateFieldType.LABELS,
                             id=uuid.UUID('76faae5f-b1e4-47f4-9e3f-ed8497f6c6d3'))
for trait in positive_traits:
    traits_field.selections.append(SelectionItem(trait, meta={'positive': True}))
for trait in negative_traits:
    traits_field.selections.append(SelectionItem(trait, meta={'positive': False}))

_enneagram_choices = {}
for item in enneagram_field.selections:
    _enneagram_choices[item.text] = item

goal_field = TemplateField('Goal', type=TemplateFieldType.SMALL_TEXT,
                           id=uuid.UUID('5e6bf763-6fa1-424a-b011-f5974290a32a'),
                           placeholder='Character goal throughout the story')
misbelief_field = TemplateField('Misbelief', type=TemplateFieldType.SMALL_TEXT,
                                id=uuid.UUID('32feaa23-acbf-4990-b99f-429747824a0b'),
                                placeholder='The misbelief/lie the character believes in')
fear_field = TemplateField('Fear', type=TemplateFieldType.SMALL_TEXT, emoji=':face_screaming_in_fear:',
                           placeholder='Fear (select Enneagram to autofill)',
                           id=uuid.UUID('d03e91bf-bc58-441a-ae81-a7764c4d7e25'), show_label=False)
desire_field = TemplateField('Desire', type=TemplateFieldType.SMALL_TEXT, emoji=':star-struck:',
                             placeholder='Desire (select Enneagram to autofill)',
                             id=uuid.UUID('92729dda-ec8c-4a61-9ed3-039c12c10ba8'), show_label=False)
role_field = TemplateField('Role', type=TemplateFieldType.TEXT_SELECTION,
                           id=uuid.UUID('131b9de6-ac95-4db5-b9a1-33200100b676'),
                           selections=[SelectionItem('Protagonist', icon='fa5s.chess-king', icon_color='#00798c'),
                                       SelectionItem('', type=SelectionItemType.SEPARATOR),
                                       SelectionItem('Antagonist', icon='mdi.guy-fawkes-mask', icon_color='#bc412b'),
                                       SelectionItem('Villain', icon='mdi.emoticon-devil', icon_color='#694966'),
                                       SelectionItem('Contagonist', icon='mdi.biohazard', icon_color='#ea9010'),
                                       SelectionItem('Henchmen', icon='mdi.shuriken', icon_color='#596475'),
                                       SelectionItem('', type=SelectionItemType.SEPARATOR),
                                       SelectionItem('Mentor', icon='mdi.compass-rose', icon_color='#80ced7'),
                                       SelectionItem('Confidant', icon='fa5s.user-friends', icon_color='#304d6d'),
                                       SelectionItem('Sidekick', icon='ei.asl', icon_color='#b0a990'),
                                       SelectionItem('Love Interest', icon='ei.heart', icon_color='#d1495b'),
                                       SelectionItem('', type=SelectionItemType.SEPARATOR),
                                       SelectionItem('Foil', icon='fa5s.yin-yang', icon_color='#947eb0'),
                                       SelectionItem('', type=SelectionItemType.SEPARATOR),
                                       SelectionItem('Secondary', icon='fa5s.chess-knight', icon_color='#619b8a'),
                                       SelectionItem('', type=SelectionItemType.SEPARATOR),
                                       SelectionItem('Tertiary', icon='mdi.chess-pawn', icon_color='#886f68'),
                                       ], compact=True)

_role_choices = {}
for item in role_field.selections:
    _role_choices[item.text] = item


class HAlignment(Enum):
    DEFAULT = 0
    LEFT = Qt.AlignLeft
    RIGHT = Qt.AlignRight
    CENTER = Qt.AlignHCenter
    JUSTIFY = Qt.AlignJustify


class VAlignment(Enum):
    TOP = Qt.AlignTop
    BOTTOM = Qt.AlignBottom
    CENTER = Qt.AlignVCenter


@dataclass
class ProfileElement:
    field: TemplateField
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    h_alignment: HAlignment = HAlignment.DEFAULT
    v_alignment: VAlignment = VAlignment.CENTER


@dataclass
class ProfileTemplate:
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    elements: List[ProfileElement] = field(default_factory=list)


def default_character_profiles() -> List[ProfileTemplate]:
    fields = [ProfileElement(name_field, 0, 0),
              ProfileElement(avatar_field, 0, 1, row_span=3, h_alignment=HAlignment.RIGHT),
              ProfileElement(gender_field, 1, 0, v_alignment=VAlignment.BOTTOM),
              ProfileElement(age_field, 2, 0, v_alignment=VAlignment.TOP),
              ProfileElement(role_field, 3, 0, v_alignment=VAlignment.BOTTOM),
              ProfileElement(goal_field, 4, 0, col_span=2, v_alignment=VAlignment.TOP),
              ProfileElement(enneagram_field, 5, 0),
              ProfileElement(mbti_field, 5, 1),
              ProfileElement(desire_field, 6, 0),
              ProfileElement(fear_field, 6, 1),
              ProfileElement(traits_field, 7, 0, col_span=2),
              ]
    return [ProfileTemplate(title='Default character template',
                            id=uuid.UUID('6e89c683-c132-469b-a75c-6712af7c339d'),
                            elements=fields)]


@dataclass
class Novel(NovelDescriptor):
    story_structure: StoryStructure = default_story_structures[0]
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
    dramatic_questions: List[DramaticQuestion] = field(default_factory=list)
    chapters: List[Chapter] = field(default_factory=list)
    stages: List[SceneStage] = field(default_factory=default_stages)
    character_profiles: List[ProfileTemplate] = field(default_factory=default_character_profiles)
    conflicts: List[Conflict] = field(default_factory=list)

    def update_from(self, updated_novel: 'Novel'):
        self.title = updated_novel.title
        self.scenes.clear()
        self.scenes.extend(updated_novel.scenes)
        self.characters.clear()
        self.characters.extend(updated_novel.characters)
        self.chapters.clear()
        self.chapters.extend(updated_novel.chapters)
        self.dramatic_questions.clear()
        self.dramatic_questions.extend(updated_novel.dramatic_questions)
        self.stages.clear()
        self.stages.extend(updated_novel.stages)
        self.character_profiles.clear()
        self.character_profiles.extend(updated_novel.character_profiles)

    def pov_characters(self) -> List[Character]:
        pov_ids = set()
        povs: List[Character] = []
        for scene in self.scenes:
            if scene.pov and str(scene.pov.id) not in pov_ids:
                povs.append(scene.pov)
                pov_ids.add(str(scene.pov.id))

        return povs


@dataclass
class Task:
    message: str
    reference: Optional[Any] = None
