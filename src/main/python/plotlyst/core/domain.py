"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

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
# flake8: noqa
import copy
import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Any, Dict

from PyQt6.QtCore import Qt
from dataclasses_json import dataclass_json, Undefined, config
from overrides import overrides

from src.main.python.plotlyst.core.template import SelectionItem, exclude_if_empty, exclude_if_black, enneagram_field, \
    mbti_field, ProfileTemplate, default_character_profiles, default_location_profiles, enneagram_choices, \
    mbti_choices, Role, summary_field, exclude_if_false
from src.main.python.plotlyst.env import app_env


@dataclass
class TemplateValue:
    id: uuid.UUID
    value: Any
    ignored: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    notes: str = field(default='', metadata=config(exclude=exclude_if_empty))

    @overrides
    def __eq__(self, other: 'TemplateValue'):
        if isinstance(other, TemplateValue):
            return self.id == other.id and self.value == other.value
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


@dataclass
class Event:
    keyphrase: str
    synopsis: str
    conflicts: List['Conflict'] = field(default_factory=list)
    emotion: int = 0


@dataclass
class Comment:
    text: str
    created_at: datetime = datetime.now()
    major: bool = False
    resolved: bool = False
    character: Optional['Character'] = None


@dataclass
class Topic:
    text: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    icon: str = field(default='', metadata=config(exclude=exclude_if_empty))
    icon_color: str = field(default='black', metadata=config(exclude=exclude_if_black))
    description: str = field(default='', metadata=config(exclude=exclude_if_empty))

    @overrides
    def __eq__(self, other: 'Topic'):
        if isinstance(other, Topic):
            return self.id == other.id and self.text == other.text
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


class AgePeriod(Enum):
    BABY = 0
    CHILD = 1
    TEENAGER = 2
    ADULT = 3


class BackstoryEventType(Enum):
    Event = 'event'
    Birthday = 'birth'
    Education = 'education'
    Job = 'fa5s.briefcase'
    Love = 'love'
    Family = 'family'
    Home = 'home'
    Friendship = 'friendship'
    Fortune = 'fortune'
    Promotion = 'promotion'
    Award = 'award'
    Death = 'death'
    Violence = 'violence'
    Accident = 'accident'
    Crime = 'crime'
    Catastrophe = 'catastrophe'
    Loss = 'loss'
    Medical = 'medical'
    Injury = 'injury'
    Breakup = 'breakup'
    Farewell = 'farewell'
    Travel = 'travel'
    Game = 'game'
    Sport = 'sport'
    Gift = 'gift'


@dataclass
class BackstoryEvent(Event):
    type: BackstoryEventType = BackstoryEventType.Event
    type_icon: str = 'ri.calendar-event-fill'
    type_color: str = 'darkBlue'
    follow_up: bool = False


@dataclass
class CharacterGoal:
    goal_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    support: bool = True
    children: List['CharacterGoal'] = field(default_factory=list)

    def goal(self, novel: 'Novel') -> Optional['Goal']:
        for goal_ in novel.goals:
            if goal_.id == self.goal_id:
                return goal_

    @overrides
    def __eq__(self, other: 'CharacterGoal'):
        if isinstance(other, CharacterGoal):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


@dataclass
class CharacterPlan:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    summary: str = ''
    external: bool = True
    goals: List[CharacterGoal] = field(default_factory=list)

    @overrides
    def __eq__(self, other: 'CharacterPlan'):
        if isinstance(other, CharacterPlan):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


MALE = 'male'
FEMALE = 'female'
TRANSGENDER = 'transgender'
NON_BINARY = 'non-binary'
GENDERLESS = 'genderless'


@dataclass
class AvatarPreferences:
    use_image: bool = True
    use_initial: bool = False
    use_role: bool = False
    use_custom_icon: bool = False
    icon: str = field(default='', metadata=config(exclude=exclude_if_empty))
    icon_color: str = field(default='black', metadata=config(exclude=exclude_if_black))

    def allow_initial(self):
        self.__allow(initial=True)

    def allow_image(self):
        self.__allow(image=True)

    def allow_role(self):
        self.__allow(role=True)

    def allow_custom_icon(self):
        self.__allow(custom=True)

    def __allow(self, image: bool = False, initial: bool = False, role: bool = False, custom: bool = False):
        self.use_image = image
        self.use_initial = initial
        self.use_role = role
        self.use_custom_icon = custom


@dataclass
class BigFiveFacet:
    name: str


@dataclass
class BigFiveDimension:
    name: str
    color: str = 'black'
    icon: str = ''
    facets: List[BigFiveFacet] = field(default_factory=list)

    @overrides
    def __eq__(self, other: 'BigFiveDimension'):
        if isinstance(other, BigFiveDimension):
            return self.name == other.name
        return False

    @overrides
    def __hash__(self):
        return hash(self.name)


agreeableness = BigFiveDimension('agreeableness', color='#8ecae6', icon='fa5s.thumbs-up',
                                 facets=[
                                     BigFiveFacet('trust'),
                                     BigFiveFacet('straightforwardness'),
                                     BigFiveFacet('altruism'),
                                     BigFiveFacet('compliance'),
                                     BigFiveFacet('modesty'),
                                     BigFiveFacet('tender-mindedness'),
                                 ])
neuroticism = BigFiveDimension('neuroticism', color='#e63946', icon='mdi6.head-flash',
                               facets=[
                                   BigFiveFacet('anxiety'),
                                   BigFiveFacet('depression'),
                                   BigFiveFacet('impulsiveness'),
                                   BigFiveFacet('hostility'),
                                   BigFiveFacet('vulnerability'),
                                   BigFiveFacet('self-consciousness'),
                               ])
extroversion = BigFiveDimension('extroversion', color='#a7c957', icon='fa5s.people-arrows',
                                facets=[
                                    BigFiveFacet('warmth'),
                                    BigFiveFacet('gregariousness'),
                                    BigFiveFacet('assertiveness'),
                                    BigFiveFacet('activity'),
                                    BigFiveFacet('excitement-seeking'),
                                    BigFiveFacet('positive emotions'),
                                ])
openness = BigFiveDimension('openness', color='#e9c46a', icon='mdi.head-lightbulb',
                            facets=[
                                BigFiveFacet('fantasy'),
                                BigFiveFacet('aesthetics'),
                                BigFiveFacet('feelings'),
                                BigFiveFacet('actions'),
                                BigFiveFacet('ideas'),
                                BigFiveFacet('values'),
                            ])
conscientiousness = BigFiveDimension('conscientiousness', color='#cdb4db', icon='mdi.head-cog-outline',
                                     facets=[
                                         BigFiveFacet('competence'),
                                         BigFiveFacet('order'),
                                         BigFiveFacet('dutifulness'),
                                         BigFiveFacet('achievement striving'),
                                         BigFiveFacet('self-discipline'),
                                         BigFiveFacet('deliberation'),
                                     ])


def default_big_five_values() -> Dict[str, List[int]]:
    return {
        agreeableness.name: [50, 50, 50, 50, 50, 50],
        neuroticism.name: [50, 50, 50, 50, 50, 50],
        extroversion.name: [50, 50, 50, 50, 50, 50],
        openness.name: [50, 50, 50, 50, 50, 50],
        conscientiousness.name: [50, 50, 50, 50, 50, 50]
    }


@dataclass
class CharacterPreferences:
    avatar: AvatarPreferences = field(default_factory=AvatarPreferences)


@dataclass
class Character:
    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    gender: str = ''
    role: Optional[Role] = None
    age: Optional[int] = None
    occupation: Optional[str] = None
    avatar: Optional[Any] = None
    template_values: List[TemplateValue] = field(default_factory=list)
    disabled_template_headers: Dict[str, bool] = field(default_factory=dict)
    backstory: List[BackstoryEvent] = field(default_factory=list)
    plans: List[CharacterPlan] = field(default_factory=list)
    document: Optional['Document'] = None
    journals: List['Document'] = field(default_factory=list)
    prefs: CharacterPreferences = field(default_factory=CharacterPreferences)
    topics: List[TemplateValue] = field(default_factory=list)
    big_five: Dict[str, List[int]] = field(default_factory=default_big_five_values)

    def enneagram(self) -> Optional[SelectionItem]:
        for value in self.template_values:
            if value.id == enneagram_field.id:
                return enneagram_choices.get(value.value)

    def mbti(self) -> Optional[SelectionItem]:
        for value in self.template_values:
            if value.id == mbti_field.id:
                return mbti_choices.get(value.value)

    def summary(self) -> str:
        for value in self.template_values:
            if value.id == summary_field.id:
                return value.value

        return ''

    def set_summary(self, summary: str):
        for tmpl_value in self.template_values:
            if tmpl_value.id == summary_field.id:
                tmpl_value.value = summary
                break

    def is_major(self):
        return self.role and self.role.is_major()

    def is_secondary(self):
        return self.role and self.role.is_secondary()

    def is_minor(self) -> bool:
        return self.role and self.role.is_minor()

    def flatten_goals(self) -> List[CharacterGoal]:
        all_goals = []
        for plan in self.plans:
            for goal in plan.goals:
                all_goals.append(goal)
                for subgoal in goal.children:
                    all_goals.append(subgoal)

        return all_goals

    @overrides
    def __eq__(self, other: 'Character'):
        if isinstance(other, Character):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


class PlaceholderCharacter(Character):
    pass


class ChapterType(Enum):
    Prologue = 0
    Epilogue = 1
    Interlude = 2


@dataclass
class Chapter:
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    type: Optional[ChapterType] = field(default=None, metadata=config(exclude=exclude_if_empty))

    def sid(self) -> str:
        return str(self.id)

    def display_name(self) -> str:
        if self.type is None:
            return self.title
        else:
            return self.type.name

    @overrides
    def __eq__(self, other: 'Chapter'):
        if isinstance(other, Chapter):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(id))


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


class StoryBeatType(Enum):
    BEAT = 'beat'
    CONTAINER = 'container'


def exclude_if_beat(value):
    return value == StoryBeatType.BEAT


@dataclass
class StoryBeat:
    text: str
    act: int
    description: str = ''
    type: StoryBeatType = field(default=StoryBeatType.BEAT, metadata=config(exclude=exclude_if_beat))
    ends_act: bool = field(default=False, metadata=config(exclude=exclude_if_empty))
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    icon: str = ''
    icon_color: str = field(default='black', metadata=config(exclude=exclude_if_black))
    percentage: int = 0
    percentage_end: int = field(default=0, metadata=config(exclude=exclude_if_empty))
    enabled: bool = True
    notes: str = field(default='', metadata=config(exclude=exclude_if_empty))

    @overrides
    def __eq__(self, other: 'StoryBeat'):
        if isinstance(other, StoryBeat):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(id))


@dataclass
class SceneStage(SelectionItem):
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    @overrides
    def __eq__(self, other: 'SceneStage'):
        if isinstance(other, SceneStage):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(id))


@dataclass
class DramaticQuestion(SelectionItem):
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    @overrides
    def __eq__(self, other: 'DramaticQuestion'):
        if isinstance(other, DramaticQuestion):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(id))


class PlotType(Enum):
    Main = 'main'
    Internal = 'internal'
    Subplot = 'subplot'
    Relation = 'relation'
    Global = 'global'


@dataclass
class PlotValue(SelectionItem):
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    negative: str = ''

    @overrides
    def __eq__(self, other: 'PlotValue'):
        if isinstance(other, PlotValue):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(id))


class PlotPrincipleType(Enum):
    GOAL = 0
    ANTAGONIST = 1
    CONFLICT = 2
    QUESTION = 8
    STAKES = 9
    THEME = 10
    POSITIVE_CHANGE = 11
    NEGATIVE_CHANGE = 12
    DESIRE = 13
    NEED = 14
    INTERNAL_CONFLICT = 15
    EXTERNAL_CONFLICT = 16
    FLAW = 17


@dataclass
class PlotPrinciple:
    type: PlotPrincipleType
    value: Any = None
    is_set: bool = False


class PlotEventType(Enum):
    PROGRESS = 0
    SETBACK = 2
    CRISIS = 3
    COST = 4
    TOOL = 5


@dataclass
class PlotEvent:
    text: str
    type: PlotEventType


# must add to the subclass:
#    character_id: Optional[uuid.UUID] = None
#    def __post_init__(self):
#        self._character: Optional[Character] = None
class CharacterBased(ABC):
    def set_character(self, character: Optional[Character]):
        if character is None:
            self.reset_character()
        else:
            self.character_id = character.id
            self._character = character

    def reset_character(self):
        self.character_id = None
        self._character = None

    def character(self, novel: 'Novel') -> Optional[Character]:
        if not self.character_id:
            return None
        if not self._character:
            for c in novel.characters:
                if c.id == self.character_id:
                    self._character = c
                    break

        return self._character


class SceneBased(ABC):

    def set_scene(self, scene: Optional['Scene']):
        if scene is None:
            self.scene_id = None
        else:
            self.scene_id = scene.id

    def scene(self, novel: 'Novel') -> Optional['Scene']:
        if not self.scene_id:
            return None
        if not self._scene:
            for s in novel.scenes:
                if s.id == self.scene_id:
                    return s


def default_plot_value() -> PlotValue:
    return PlotValue('Progress', icon='fa5s.chart-line')


class PlotProgressionItemType(Enum):
    BEGINNING = 0
    MIDDLE = 1
    ENDING = 2
    EVENT = 3


@dataclass
class PlotProgressionItem:
    type: PlotProgressionItemType
    text: str = ''


class StorylineLinkType(Enum):
    Connection = auto()
    Catalyst = auto()
    Impact = auto()
    Contrast = auto()
    Reflect_char = auto()
    Reflect_plot = auto()
    Reveal = auto()
    Resolve = auto()
    Compete = auto()

    def icon(self) -> str:
        if self == StorylineLinkType.Catalyst:
            return 'fa5s.vial'
        elif self == StorylineLinkType.Impact:
            return 'mdi.motion-outline'
        elif self == StorylineLinkType.Contrast:
            return 'ei.adjust'
        elif self == StorylineLinkType.Reflect_char:
            return 'msc.mirror'
        elif self == StorylineLinkType.Reflect_plot:
            return 'msc.mirror'
        elif self == StorylineLinkType.Resolve:
            return 'mdi.bullseye-arrow'
        # elif self == StorylineLinkType.Parallel:
        #     return 'fa5s.grip-lines'
        elif self == StorylineLinkType.Compete:
            return 'ph.arrows-in-line-horizontal'
        # elif self == StorylineLinkType.Complicate:
        #     return 'mdi.sword-cross'
        # elif self == StorylineLinkType.Converge:
        #     return 'ri.git-pull-request-fill'
        return 'fa5s.link'

    def desc(self) -> str:
        if self == StorylineLinkType.Catalyst:
            return 'A storyline triggers the events in an other storyline'
        elif self == StorylineLinkType.Impact:
            return 'A storyline impacts or influences the events in an other storyline'
        elif self == StorylineLinkType.Contrast:
            return 'The storylines contrast each other in any way, e.g.,theme, tone, or pacing'
        elif self == StorylineLinkType.Reflect_char:
            return "The relationship plot reflects the character's changes"
        elif self == StorylineLinkType.Reflect_plot:
            return "The relationship plot reflects larger plot themes of conflicts through character interactions"
        elif self == StorylineLinkType.Reveal:
            return "The character's changes reveal the true nature of a relationship plot"
        elif self == StorylineLinkType.Resolve:
            return "Only through the character's changes the plot can be resolved"
        elif self == StorylineLinkType.Compete:
            return 'Two storylines compete against each other, often for a common goal'
        return 'How does the storyline connect to the other one?'

    def placeholder(self) -> str:
        if self == StorylineLinkType.Catalyst:
            return ''
        elif self == StorylineLinkType.Impact:
            return ''
        elif self == StorylineLinkType.Contrast:
            return ''
        elif self == StorylineLinkType.Reflect_char:
            return ''
        elif self == StorylineLinkType.Reflect_plot:
            return ''
        elif self == StorylineLinkType.Resolve:
            return ''
        elif self == StorylineLinkType.Compete:
            return ''
        return 'How does the storyline connect to the other one?'


@dataclass
class StorylineLink:
    source_id: uuid.UUID
    target_id: uuid.UUID
    type: StorylineLinkType
    text: str = ''


@dataclass
class Plot(SelectionItem, CharacterBased):
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    plot_type: PlotType = PlotType.Main
    values: List[PlotValue] = field(default_factory=list)
    character_id: Optional[uuid.UUID] = None
    relation_character_id: Optional[uuid.UUID] = None
    question: str = ''
    principles: List[PlotPrinciple] = field(default_factory=list)
    events: List[PlotEvent] = field(default_factory=list)
    default_value: PlotValue = field(default_factory=default_plot_value)
    default_value_enabled: bool = True
    progression: List[PlotProgressionItem] = field(default_factory=list)
    links: List[StorylineLink] = field(default_factory=list)

    def __post_init__(self):
        self._character: Optional[Character] = None
        self._relation_character: Optional[Character] = None

    def relation_character(self, novel: 'Novel') -> Optional[Character]:
        if not self.relation_character_id:
            return None
        if not self._relation_character:
            for c in novel.characters:
                if c.id == self.relation_character_id:
                    self._relation_character = c
                    break

        return self._relation_character

    def set_relation_character(self, character: Optional[Character]):
        if character is None:
            self.reset_character()
        else:
            self.relation_character_id = character.id
            self._relation_character = character

    @overrides
    def reset_character(self):
        super().reset_character()
        self.relation_character_id = None
        self._relation_character = None

    @overrides
    def __eq__(self, other: 'Plot'):
        if isinstance(other, Plot):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(id))


class ConflictType(Enum):
    CHARACTER = 0
    SOCIETY = 1
    NATURE = 2
    TECHNOLOGY = 3
    SUPERNATURAL = 4
    SELF = 5


@dataclass
class Conflict(SelectionItem, CharacterBased):
    type: ConflictType = ConflictType.CHARACTER
    character_id: Optional[uuid.UUID] = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    conflicting_character_id: Optional[uuid.UUID] = None

    def __post_init__(self):
        self._character: Optional[Character] = None
        self._conflicting_character: Optional[Character] = None

    def conflicting_character(self, novel: 'Novel') -> Optional[Character]:
        if not self.conflicting_character_id:
            return None
        if not self._conflicting_character:
            for c in novel.characters:
                if c.id == self.conflicting_character_id:
                    self._conflicting_character = c
                    break

        return self._conflicting_character

    @overrides
    def __eq__(self, other: 'Conflict'):
        if isinstance(other, Conflict):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


@dataclass
class Goal(SelectionItem):
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    description: str = ''

    @overrides
    def __eq__(self, other: 'Goal'):
        if isinstance(other, Goal):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


@dataclass
class ScenePlotValueCharge:
    plot_value_id: uuid.UUID
    charge: int

    def plot_value(self, plot: Plot) -> Optional[PlotValue]:
        for v in plot.values:
            if v.id == self.plot_value_id:
                return v


@dataclass
class ScenePlotReferenceData:
    comment: str = field(default='', metadata=config(exclude=exclude_if_empty))
    values: List[ScenePlotValueCharge] = field(default_factory=list)


@dataclass
class ScenePlotReference:
    plot: Plot
    data: ScenePlotReferenceData = field(default_factory=ScenePlotReferenceData)


class SceneStructureItemType(Enum):
    ACTION = 0
    CONFLICT = 1
    CLIMAX = 2
    REACTION = 3
    DILEMMA = 4
    DECISION = 5
    BEAT = 6
    INCITING_INCIDENT = 7
    RISING_ACTION = 8
    CHOICE = 9
    TICKING_CLOCK = 10
    HOOK = 11
    EXPOSITION = 12
    TURN = 13
    MYSTERY = 14
    REVELATION = 15
    SETUP = 16
    EMOTION = 17
    SUMMARY = 18
    PROGRESS = 19
    SETBACK = 20
    RESOLUTION = 21
    BUILDUP = 22
    DISTURBANCE = 23
    FALSE_VICTORY = 24


class SceneOutcome(Enum):
    DISASTER = 0
    RESOLUTION = 1
    TRADE_OFF = 2
    MOTION = 3

    @staticmethod
    def to_str(outcome: 'SceneOutcome') -> str:
        if outcome == SceneOutcome.TRADE_OFF:
            return 'Trade-off outcome'
        elif outcome == SceneOutcome.MOTION:
            return 'Set into motion'
        return outcome.name.lower().capitalize() + ' outcome'


@dataclass
class SceneStructureItem:
    type: SceneStructureItemType
    text: str = ''
    percentage: float = 0.0
    emotion: str = field(default='', metadata=config(exclude=exclude_if_empty))
    meta: Dict[str, Any] = field(default_factory=dict, metadata=config(exclude=exclude_if_empty))

    @property
    def outcome(self) -> Optional[SceneOutcome]:
        if 'outcome' in self.meta.keys():
            return SceneOutcome(self.meta['outcome'])

    @outcome.setter
    def outcome(self, value: SceneOutcome):
        self.meta['outcome'] = value.value


@dataclass
class ConflictReference:
    conflict_id: uuid.UUID
    message: str = ''
    intensity: int = 1

    def conflict(self, novel: 'Novel') -> Optional[Conflict]:
        for conflict in novel.conflicts:
            if conflict.id == self.conflict_id:
                return conflict


class Motivation(Enum):
    PHYSIOLOGICAL = 0
    SAFETY = 1
    BELONGING = 2
    ESTEEM = 3
    SELF_ACTUALIZATION = 4
    SELF_TRANSCENDENCE = 5

    def display_name(self) -> str:
        if self == Motivation.PHYSIOLOGICAL:
            return 'Physiological needs'
        elif self == Motivation.SAFETY:
            return 'Security and safety'
        elif self == Motivation.BELONGING:
            return 'Belonging and love'
        elif self == Motivation.ESTEEM:
            return 'Esteem and success'
        else:
            return self.name.lower().replace('_', '-').capitalize()

    def icon(self) -> str:
        if self == Motivation.PHYSIOLOGICAL:
            return 'mdi.water'
        elif self == Motivation.SAFETY:
            return 'mdi.shield-half-full'
        elif self == Motivation.BELONGING:
            return 'fa5s.hand-holding-heart'
        elif self == Motivation.ESTEEM:
            return 'fa5s.award'
        elif self == Motivation.SELF_ACTUALIZATION:
            return 'mdi.yoga'
        elif self == Motivation.SELF_TRANSCENDENCE:
            return 'mdi6.meditation'

    def color(self) -> str:
        if self == Motivation.PHYSIOLOGICAL:
            return '#023e8a'
        elif self == Motivation.SAFETY:
            return '#8900f2'
        elif self == Motivation.BELONGING:
            return '#d00000'
        elif self == Motivation.ESTEEM:
            return '#00b4d8'
        elif self == Motivation.SELF_ACTUALIZATION:
            return '#52b788'
        elif self == Motivation.SELF_TRANSCENDENCE:
            return '#c38e70'


@dataclass
class GoalReference:
    character_goal_id: uuid.UUID
    message: str = ''
    stakes: Dict[int, int] = field(default_factory=dict, metadata=config(exclude=exclude_if_empty))

    def goal(self, character: Character) -> CharacterGoal:
        for goal_ in character.flatten_goals():
            if goal_.id == self.character_goal_id:
                return goal_


@dataclass
class TagReference:
    tag_id: uuid.UUID
    message: str = ''


@dataclass
class SceneStructureAgenda(CharacterBased):
    character_id: Optional[uuid.UUID] = None
    conflict_references: List[ConflictReference] = field(default_factory=list)
    goal_references: List[GoalReference] = field(default_factory=list)
    intensity: int = field(default=0, metadata=config(exclude=exclude_if_empty))
    emotion: Optional[int] = None
    motivations: Dict[int, int] = field(default_factory=dict, metadata=config(exclude=exclude_if_empty))
    story_elements: List['StoryElement'] = field(default_factory=list)

    def __post_init__(self):
        self._character: Optional[Character] = None

    def conflicts(self, novel: 'Novel') -> List[Conflict]:
        conflicts_ = []
        for id_ in [x.conflict_id for x in self.conflict_references]:
            for conflict in novel.conflicts:
                if conflict.id == id_:
                    conflicts_.append(conflict)

        return conflicts_

    def remove_conflict(self, conflict: Conflict):
        self.conflict_references = [x for x in self.conflict_references if x.conflict_id != conflict.id]

    def remove_goal(self, char_goal: CharacterGoal):
        self.goal_references = [x for x in self.goal_references if x.character_goal_id != char_goal.id]

    def goals(self, character: Character) -> List[CharacterGoal]:
        goals_ = character.flatten_goals()
        agenda_goal_ids = [x.character_goal_id for x in self.goal_references]
        return [x for x in goals_ if x.id in agenda_goal_ids]


@dataclass
class SceneStoryBeat:
    structure_id: uuid.UUID
    beat_id: uuid.UUID
    character_id: Optional[uuid.UUID] = None

    def beat(self, structure: 'StoryStructure') -> Optional[StoryBeat]:
        if self.structure_id == structure.id and self.character_id == structure.character_id:
            return next((b for b in structure.beats if b.id == self.beat_id), None)

    @staticmethod
    def of(structure: 'StoryStructure', beat: StoryBeat) -> 'SceneStoryBeat':
        return SceneStoryBeat(structure.id, beat.id, structure.character_id)


class ReaderPosition(Enum):
    SUPERIOR = 0
    INFERIOR = 1


class InformationAcquisition(Enum):
    DISCOVERY = 0
    REVELATION = 1


@dataclass
class SceneDrive:
    worldbuilding: int = field(default=0, metadata=config(exclude=exclude_if_empty))
    tension: int = field(default=0, metadata=config(exclude=exclude_if_empty))
    new_information: Optional[InformationAcquisition] = field(default=None, metadata=config(exclude=exclude_if_empty))
    reader_position: Optional[ReaderPosition] = field(default=None, metadata=config(exclude=exclude_if_empty))
    deus_ex_machina: bool = field(default=False, metadata=config(exclude=exclude_if_false))


class ScenePurposeType(Enum):
    Story = 'story'
    Reaction = 'reaction'
    Character = 'character'
    Emotion = 'emotion'
    Setup = 'setup'
    Exposition = 'exposition'
    Other = 'other'


@dataclass
class ScenePurpose:
    type: ScenePurposeType
    display_name: str
    keywords: List[str] = field(default_factory=list)
    include: List[ScenePurposeType] = field(default_factory=list)
    help_include: str = ''
    pacing: str = ''


advance_story_scene_purpose = ScenePurpose(ScenePurposeType.Story, 'Advance\nstory',
                                           keywords=['goal', 'conflict', 'action', 'outcome', 'tension', 'revelation',
                                                     'mystery', 'catalyst'],
                                           include=[ScenePurposeType.Character, ScenePurposeType.Emotion,
                                                    ScenePurposeType.Setup],
                                           pacing='fast-medium')
reaction_story_scene_purpose = ScenePurpose(ScenePurposeType.Reaction, 'Reaction',
                                            keywords=['reflection', 'dilemma', 'decision', 'introspection', 'analysis',
                                                      'new goal'],
                                            include=[ScenePurposeType.Character, ScenePurposeType.Emotion],
                                            pacing='medium-slow')
character_story_scene_purpose = ScenePurpose(ScenePurposeType.Character, 'Character\ndevelopment',
                                             keywords=['internal conflict', 'relations'],
                                             include=[ScenePurposeType.Emotion])
emotion_story_scene_purpose = ScenePurpose(ScenePurposeType.Emotion, 'Emotion',
                                           keywords=['mood', 'atmosphere', 'emotion'])
setup_story_scene_purpose = ScenePurpose(ScenePurposeType.Setup, 'Setup',
                                         keywords=['plant', 'foreshadowing', 'setup', 'happening', 'transition'])
exposition_story_scene_purpose = ScenePurpose(ScenePurposeType.Exposition, 'Exposition',
                                              keywords=['introduction', 'description', 'information'])

scene_purposes: Dict[ScenePurposeType, ScenePurpose] = {
    ScenePurposeType.Story: advance_story_scene_purpose,
    ScenePurposeType.Reaction: reaction_story_scene_purpose,
    ScenePurposeType.Character: character_story_scene_purpose,
    ScenePurposeType.Emotion: emotion_story_scene_purpose,
    ScenePurposeType.Setup: setup_story_scene_purpose,
    ScenePurposeType.Exposition: exposition_story_scene_purpose,
}


class StoryElementType(Enum):
    Plot = 'plot'
    Arc = 'arc'
    Outcome = 'outcome'
    Consequences = 'consequences'
    Goal = 'goal'
    Motivation = 'motivation'
    Conflict = 'conflict'
    Internal_conflict = 'internal_conflict'
    Dilemma = 'dilemma'
    Impact = 'impact'
    Responsibility = 'responsibility'
    Decision = 'decision'
    Emotion = 'emotion'
    Agency = 'agency'
    Initiative = 'initiative'
    Catalyst = 'catalyst'
    Plan_change = 'plan_change'
    Collaboration = 'collaboration'
    Subtext = 'subtext'
    Event = 'event'
    Effect = 'effect'


@dataclass
class StoryElement:
    type: StoryElementType
    ref: Optional[uuid.UUID] = None
    text: str = ''
    intensity: int = field(default=0, metadata=config(exclude=exclude_if_empty))
    row: int = field(default=0, metadata=config(exclude=exclude_if_empty))
    col: int = field(default=0, metadata=config(exclude=exclude_if_empty))
    arrows: Dict[int, int] = field(default_factory=dict, metadata=config(exclude=exclude_if_empty))


@dataclass
class Scene:
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    synopsis: str = ''
    pov: Optional[Character] = None
    characters: List[Character] = field(default_factory=list)
    agendas: List[SceneStructureAgenda] = field(default_factory=list)
    wip: bool = False
    plot_values: List[ScenePlotReference] = field(default_factory=list)
    day: int = 1
    chapter: Optional[Chapter] = None
    arcs: List[CharacterArc] = field(default_factory=list)
    stage: Optional[SceneStage] = None
    beats: List[SceneStoryBeat] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    tag_references: List[TagReference] = field(default_factory=list)
    document: Optional['Document'] = None
    manuscript: Optional['Document'] = None
    drive: SceneDrive = field(default_factory=SceneDrive)
    purpose: Optional[ScenePurposeType] = None
    outcome: Optional[SceneOutcome] = None
    story_elements: List[StoryElement] = field(default_factory=list)
    structure: List[SceneStructureItem] = field(default_factory=list)

    def beat(self, novel: 'Novel') -> Optional[StoryBeat]:
        structure = novel.active_story_structure
        for b in self.beats:
            if b.structure_id == structure.id and b.character_id == structure.character_id:
                return b.beat(structure)

    def link_beat(self, structure: 'StoryStructure', beat: StoryBeat):
        self.reset_structure(structure)
        self.beats.append(SceneStoryBeat.of(structure, beat))

    def reset_structure(self, structure: 'StoryStructure'):
        self.beats[:] = [x for x in self.beats if
                         x.structure_id != structure.id and x.character_id != structure.character_id]

    def remove_beat(self, novel: 'Novel'):
        beat = self.beat(novel)
        if not beat:
            return
        beat_structure = None
        for b in self.beats:
            if b.beat_id == beat.id:
                beat_structure = b
                break
        if beat_structure:
            self.beats.remove(beat_structure)

    def pov_arc(self) -> int:
        for arc in self.arcs:
            if arc.character == self.pov:
                return arc.arc
        return NEUTRAL

    def plots(self) -> List[Plot]:
        return [x.plot for x in self.plot_values]

    def tags(self, novel: 'Novel') -> List['Tag']:
        tags_ = []
        for id_ in [x.tag_id for x in self.tag_references]:
            for tags_per_type in novel.tags.values():
                for tag in tags_per_type:
                    if tag.id == id_:
                        tags_.append(tag)

        return tags_

    def outcome_resolution(self) -> bool:
        return self.__is_outcome(SceneOutcome.RESOLUTION)

    def outcome_trade_off(self) -> bool:
        return self.__is_outcome(SceneOutcome.TRADE_OFF)

    def outcome_motion(self) -> bool:
        return self.__is_outcome(SceneOutcome.MOTION)

    def title_or_index(self, novel: 'Novel') -> str:
        return self.title if self.title else f'Scene {novel.scenes.index(self) + 1}'

    def __is_outcome(self, expected) -> bool:
        if self.outcome and self.outcome == expected:
            return True

        return False

    @overrides
    def __eq__(self, other: 'Scene'):
        if isinstance(other, Scene):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


def default_stages() -> List[SceneStage]:
    return [SceneStage('Outlined'), SceneStage('1st Draft'),
            SceneStage('2nd Draft'), SceneStage('3rd Draft'), SceneStage('4th Draft'),
            SceneStage('Edited'), SceneStage('Proofread'), SceneStage('Final')]


class WorldBuildingEntityType(Enum):
    ABSTRACT = 1
    SETTING = 2
    GROUP = 3
    ITEM = 4
    CONTAINER = 5


@dataclass
class WorldBuildingEntity:
    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    children: List['WorldBuildingEntity'] = field(default_factory=list)
    icon: str = field(default='', metadata=config(exclude=exclude_if_empty))
    icon_color: str = field(default='', metadata=config(exclude=exclude_if_empty))
    emoji: str = field(default='', metadata=config(exclude=exclude_if_empty))
    bg_color: str = field(default='', metadata=config(exclude=exclude_if_empty))
    summary: str = field(default='', metadata=config(exclude=exclude_if_empty))
    type: WorldBuildingEntityType = WorldBuildingEntityType.ABSTRACT
    notes: str = field(default='', metadata=config(exclude=exclude_if_empty))
    template_values: List[TemplateValue] = field(default_factory=list)
    topics: List[TemplateValue] = field(default_factory=list)

    @overrides
    def __eq__(self, other: 'WorldBuildingEntity'):
        if isinstance(other, WorldBuildingEntity):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class WorldBuilding:
    root_entity: WorldBuildingEntity = WorldBuildingEntity('My world', icon='mdi.globe-model', bg_color='#40916c')
    location_profiles: List[ProfileTemplate] = field(default_factory=default_location_profiles)


@dataclass
class TaskStatus(SelectionItem):
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    wip: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    resolves: bool = field(default=False, metadata=config(exclude=exclude_if_false))

    @overrides
    def __eq__(self, other: 'TaskStatus'):
        if isinstance(other, TaskStatus):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(id))


tag_characterization = SelectionItem('Characterization', icon='fa5s.user', icon_color='darkBlue')
tag_worldbuilding = SelectionItem('Worldbuilding', icon='mdi.globe-model', icon_color='#2d6a4f')
tag_brainstorming = SelectionItem('Brainstorming', icon='fa5s.brain', icon_color='#FF5733')
tag_research = SelectionItem('Research', icon='mdi.library', icon_color='#0066CC')
tag_writing = SelectionItem('Writing', icon='mdi.typewriter', icon_color='#9933CC')
tag_plotting = SelectionItem('Plotting', icon='fa5s.theater-masks', icon_color='#FF6666')
tag_theme = SelectionItem('Theme', icon='mdi.butterfly-outline', icon_color='#9d4edd')
tag_outlining = SelectionItem('Outlining', icon='fa5s.list', icon_color='#99CC00')
tag_revision = SelectionItem('Revision', icon='mdi.clipboard-edit-outline', icon_color='#FF9933')
tag_drafting = SelectionItem('Drafting', icon='fa5s.dog', icon_color='#66CC33')
tag_editing = SelectionItem('Editing', icon='fa5s.cat', icon_color='#ff758f')
tag_collect_feedback = SelectionItem('Collect feedback', icon='msc.feedback', icon_color='#5e60ce')
tag_publishing = SelectionItem('Publishing', icon='fa5s.cloud-upload-alt', icon_color='#FF9900')
tag_marketing = SelectionItem('Marketing', icon='fa5s.bullhorn', icon_color='#FF3366')
tag_book_cover_design = SelectionItem('Book cover design', icon='fa5s.book', icon_color='#FF66CC')
tag_formatting = SelectionItem('Formatting', icon='mdi.format-pilcrow', icon_color='#006600')

_tags = [
    tag_characterization, tag_worldbuilding, tag_brainstorming, tag_research, tag_writing,
    tag_plotting, tag_theme, tag_outlining, tag_revision, tag_drafting, tag_editing,
    tag_collect_feedback, tag_publishing, tag_marketing, tag_book_cover_design, tag_formatting
]
task_tags: Dict[str, SelectionItem] = {}
for tag in _tags:
    task_tags[tag.text] = tag


@dataclass
class Task(CharacterBased):
    title: str
    status_ref: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    creation_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    summary: str = field(default='', metadata=config(exclude=exclude_if_empty))
    character_id: Optional[uuid.UUID] = None
    tags: List[str] = field(default_factory=list, metadata=config(exclude=exclude_if_empty))

    def __post_init__(self):
        if self.creation_date is None:
            self.creation_date = datetime.now()
        self._character: Optional[Character] = None

    def creation_date_str(self):
        return self.creation_date.strftime("%Y-%m-%d %H:%M:%S")

    def resolved_date_str(self):
        return self.resolved_date.strftime("%Y-%m-%d %H:%M:%S") if self.resolved_date else ''

    def update_resolved_date(self):
        self.resolved_date = datetime.now()

    @overrides
    def __eq__(self, other: 'Task'):
        if isinstance(other, Task):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(id))


def default_task_statues() -> List[TaskStatus]:
    return [TaskStatus('To Do', color_hexa='#0077b6'), TaskStatus('In Progress', color_hexa='#9f86c0', wip=True),
            TaskStatus('Done', color_hexa='#588157', resolves=True)]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Board:
    tasks: List[Task] = field(default_factory=list)
    statuses: List[TaskStatus] = field(default_factory=default_task_statues)


@dataclass
class StoryStructure(CharacterBased):
    title: str
    icon: str = ''
    icon_color: str = 'black'
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    beats: List[StoryBeat] = field(default_factory=list)
    custom: bool = False
    active: bool = False
    character_id: Optional[uuid.UUID] = None
    acts_text: Dict[int, str] = field(default_factory=dict)

    def __post_init__(self):
        self._character: Optional[Character] = None

    def act_beats(self) -> List[StoryBeat]:
        return [x for x in self.beats if x.ends_act]


hook_beat = StoryBeat(text='Hook',
                      id=uuid.UUID('40365047-e7df-4543-8816-f9f8dcce12da'),
                      icon='mdi.hook',
                      icon_color='#829399',
                      description="Raises curiosity and hooks the reader's attention. May hint at what kind of story the reader can expect.",
                      act=1, percentage=1)
motion_beat = StoryBeat(text='Motion',
                        id=uuid.UUID('f9120632-3e27-405e-b404-543f9c5b12ca'),
                        icon='mdi.motion-outline',
                        icon_color='#d4a373',
                        description='Sets the story in motion with enough intrigue to create narrative drive, but without establishing the story yet.',
                        act=1, percentage=1)
disturbance_beat = StoryBeat(text='Disturbance',
                             id=uuid.UUID('a954f949-8be9-46d6-8ebf-f9f76f482944'),
                             icon='mdi.chemical-weapon',
                             icon_color='#e63946',
                             description="Disturbs the protagonist's life and sets the story in motion.",
                             act=1, percentage=1)
characteristic_moment_beat = StoryBeat(text='Characteristic Moment',
                                       id=uuid.UUID('b50c32e4-1927-4633-b5a3-9765aeaee7ad'),
                                       icon='mdi6.human-scooter',
                                       icon_color='#457b9d',
                                       description="Introduces the protagonist, highlighting their character traits and core personality, possibly flaws as well.",
                                       act=1, percentage=1)
normal_world_beat = StoryBeat(text='Normal World',
                              id=uuid.UUID('79ebc3b6-6b02-4d2d-8fdd-12274b8bb412'),
                              icon='fa5.image',
                              icon_color='#1ea896',
                              description="Establishes the setting alongside the protagonist before the first major change in the story would happen.",
                              act=1, percentage=1)

first_plot_point = StoryBeat(text='First Plot Point',
                             icon='mdi6.chevron-double-right',
                             icon_color='#2a4494',
                             description="It propels the protagonist into the central conflict.",
                             id=uuid.UUID('8d85c960-1c63-44d4-812d-545d3ba4d153'), act=1,
                             ends_act=True, percentage=20)

first_plot_point_ponr = StoryBeat(text='First Plot Point',
                                  icon='fa5s.door-closed',
                                  icon_color='#2a4494',
                                  description="It propels the protagonist into the central conflict through the character's irreversible decision. There's no going back now.",
                                  id=uuid.UUID('d94e8ecd-c60d-4e7b-9817-47877ea1402f'), act=1,
                                  ends_act=True, percentage=20)

second_plot_point = StoryBeat(text='Second Plot Point',
                              id=uuid.UUID('95705e5e-a6b8-4abe-b2ea-426f2ae8d020'),
                              icon='mdi6.chevron-triple-right',
                              description="It propels the protagonist towards the climax to face the main conflict, often through a new twist, revelation, or turning point.",
                              icon_color='#6a0136',
                              act=2, ends_act=True, percentage=80)

second_plot_point_aha = StoryBeat(text='Aha moment',
                                  id=uuid.UUID('77e05b3c-27c3-42b2-bcbc-1f46dfc85d73'),
                                  icon='fa5.lightbulb',
                                  description="A-ha moment.",
                                  icon_color='#6a0136',
                                  act=2, ends_act=True, percentage=80)

midpoint = StoryBeat(text='Midpoint',
                     icon='mdi.middleware-outline',
                     icon_color='#2e86ab',
                     description="Intensifies the conflict and raises the stakes by often involving a major relevation or turning point. It may shift the story into a different direction.",
                     id=uuid.UUID('3f817e10-85d1-46af-91c6-70f1ad5c0542'),
                     act=2, percentage=50)
midpoint_ponr = StoryBeat('Point of No Return',
                          icon='fa5s.door-closed',
                          icon_color='#028090',
                          description='An irreversible critical decision with significant consequences from which the protagonist has no way back.',
                          id=uuid.UUID('0630a2af-f687-4dfa-98f1-2c50a52b40cb'),
                          act=2, percentage=50)
midpoint_mirror = StoryBeat('Mirror Moment',
                            icon='mdi6.mirror-variant',
                            icon_color='#0096c7',
                            description="The protagonist's self-reflection, confronting their flaws or internal conflicts.",
                            id=uuid.UUID('94b58db9-e59f-412e-b284-b911908e443f'),
                            act=2, percentage=50
                            )
midpoint_proactive = StoryBeat('Reactive to Proactive Shift',
                               icon='mdi.account-convert',
                               icon_color='#219ebc',
                               description="The protagonist takes the initiative and takes control of the conflict instead of reacting to it.",
                               id=uuid.UUID('d7d1b457-353f-4259-92c2-0cc7da0e4b88'),
                               act=2, percentage=50
                               )
crisis = StoryBeat(text='Crisis',
                   icon='mdi.arrow-decision-outline',
                   icon_color='#ce2d4f',
                   description="The protagonist must decide between two equally bad or two irreconcilable good choices.",
                   id=uuid.UUID('466688f7-ebee-4d36-a655-83ff40e1c46d'),
                   act=3, percentage=95)

first_plot_points = (first_plot_point, first_plot_point_ponr)
midpoints = (midpoint, midpoint_ponr, midpoint_mirror, midpoint_proactive)

three_act_structure = StoryStructure(title='Three Act Structure',
                                     id=uuid.UUID('58013be5-1efb-4de4-9dd2-1433ce6edf90'),
                                     icon='mdi.numeric-3-circle-outline',
                                     icon_color='#ff7800',
                                     beats=[hook_beat,
                                            StoryBeat(text='Inciting Incident',
                                                      icon='mdi.bell-alert-outline',
                                                      icon_color='#a2ad59',
                                                      description="The first event that truly changes the protagonist's status quo and thus establishes the story. Often an external conflict is involved that raises the stakes and sets the protagonist in a new direction.",
                                                      id=uuid.UUID('a0c2d94a-b53c-485e-a279-f2548bdb38ec'),
                                                      act=1, percentage=10),
                                            first_plot_point,
                                            StoryBeat(text='First Pinch Point',
                                                      id=uuid.UUID('af024374-12e6-44dc-80e6-28f2bc0e59ed'),
                                                      icon='fa5s.thermometer-three-quarters',
                                                      description='A reminder of the power of antagonistic forces.',
                                                      icon_color='#b81365',
                                                      act=2, percentage=35),
                                            midpoint,
                                            StoryBeat(text='Second Pinch Point',
                                                      id=uuid.UUID('74087e28-b37a-4797-95bc-41d96f6a9393'),
                                                      icon='fa5s.biohazard',
                                                      description="A showcase of the full strength of antagonistic forces and a reminder of what's at stake.",
                                                      icon_color='#cd533b',
                                                      act=2, percentage=62),
                                            StoryBeat(text='Dark Moment',
                                                      icon='mdi.weather-night',
                                                      icon_color='#494368',
                                                      description="All-time low moment for the protagonist. They must feel worse than at the beginning of the story.",
                                                      id=uuid.UUID('4ded5006-c90a-4825-9de7-e16bf62017a3'), act=2,
                                                      percentage=75, enabled=False),
                                            second_plot_point,
                                            crisis,
                                            StoryBeat(text='Climax',
                                                      icon='fa5s.chevron-up',
                                                      icon_color='#ce2d4f',
                                                      description="The highest point of tension. The final confrontation between the protagonist and the antagonist. The story's main dramatic question is resolved.",
                                                      id=uuid.UUID('342eb27c-52ff-40c2-8c5e-cf563d4e38bc'),
                                                      act=3, percentage=97),
                                            StoryBeat(text='Resolution',
                                                      icon='fa5s.water',
                                                      description="An 'after' snapshot to tie up loose ends and release tension.",
                                                      icon_color='#7192be',
                                                      id=uuid.UUID('996695b1-8db6-4c68-8dc4-51bbfe720e8b'),
                                                      act=3, percentage=99),
                                            ])

save_the_cat = StoryStructure(title='Save the Cat',
                              id=uuid.UUID('1f1c4433-6afa-48e1-a8dc-f8fcb94bfede'),
                              icon='fa5s.cat',
                              beats=[StoryBeat(text='Opening Image',
                                               icon='fa5.image',
                                               icon_color='#1ea896',
                                               description="Establishes the setting and introduces the protagonist. Bonus: hints at the main character's flaws and desires.",
                                               id=uuid.UUID('249bba52-98b8-4577-8b3c-94481f6bf622'),
                                               act=1, percentage=1),
                                     StoryBeat(text='Setup',
                                               type=StoryBeatType.CONTAINER,
                                               icon='mdi.toy-brick-outline',
                                               icon_color='#02bcd4',
                                               id=uuid.UUID('7ce4345b-60eb-4cd6-98cc-7cce98028839'),
                                               act=1, percentage=1, percentage_end=10),
                                     StoryBeat(text='Theme Stated',
                                               icon='ei.idea-alt',
                                               icon_color='#f72585',
                                               description="Hints at the lesson that the protagonist will learn by the end of the story. At this point they ignore it.",
                                               id=uuid.UUID('1c8b0903-f169-48d5-bcec-3e842f360150'),
                                               act=1, percentage=5),
                                     StoryBeat(text='Catalyst',
                                               icon='fa5s.vial',
                                               icon_color='#822faf',
                                               description="The first event that truly changes the protagonist's status quo. Often external conflict is involved that raises the stakes and sets the protagonist in a new direction.",
                                               id=uuid.UUID('cc3d8641-bcdf-402b-ba84-7ff59b2cc76a'),
                                               act=1, percentage=10),
                                     StoryBeat(text='Debate',
                                               type=StoryBeatType.CONTAINER,
                                               icon='fa5s.map-signs',
                                               icon_color='#ba6f4d',
                                               id=uuid.UUID('0203696e-dc54-4a10-820a-bfdf392a82dc'),
                                               act=1, percentage=10, percentage_end=20),
                                     StoryBeat(text='Break into Two',
                                               icon='mdi6.clock-time-three-outline',
                                               icon_color='#1bbc9c',
                                               description="Start of Act 2. The protagonist enters a new world, sometimes physically, by making a decision and addressing the Catalyst event.",
                                               id=uuid.UUID('43eb267f-2840-437b-9eac-9e52d80eba2b'),
                                               act=1, ends_act=True, percentage=20),
                                     StoryBeat(text='B Story',
                                               icon='mdi.alpha-b-box',
                                               icon_color='#a6808c',
                                               description="Introduction of a new character who represents the B Story, which is the thematic or spiritual story of the protagonist's journey.",
                                               id=uuid.UUID('64229c74-5513-4391-9b45-c54ad106c137'),
                                               act=2, percentage=22),
                                     StoryBeat(text='Fun and Games',
                                               type=StoryBeatType.CONTAINER,
                                               icon='fa5s.gamepad',
                                               icon_color='#2c699a',
                                               id=uuid.UUID('490157f0-f255-4ab3-82f3-bc5cb22ce03b'),
                                               act=2, percentage=20, percentage_end=50),
                                     StoryBeat(text='Midpoint',
                                               icon='mdi.middleware-outline',
                                               icon_color='#2e86ab',
                                               description="A false defeat or false victory moment that raises the stakes. Often Story A and Story B intersect. The protagonist turns to proactive from reactive.",
                                               id=uuid.UUID('af4fb4e9-f287-47b6-b219-be75af752622'),
                                               act=2, percentage=50),
                                     StoryBeat(text='Bad Guys Close In',
                                               type=StoryBeatType.CONTAINER,
                                               icon='fa5s.biohazard',
                                               icon_color='#cd533b',
                                               id=uuid.UUID('2060c95f-dcdb-4074-a096-4b054f70d57a'),
                                               act=2, percentage=50, percentage_end=75),
                                     StoryBeat(text='All is Lost',
                                               icon='mdi.trophy-broken',
                                               icon_color='#cd533b',
                                               description='All-time low moment for the protagonist. They must feel worse than at the beginning of the story.',
                                               id=uuid.UUID('2971ce1a-eb69-4ac1-9f2d-74407e6fac92'),
                                               act=2, percentage=75),
                                     StoryBeat(text='Return to the Familiar',
                                               icon='mdi.home-circle',
                                               icon_color='#8ecae6',
                                               description="While the protagonist wallows, they often retrieve to their normal world but their old environment doesn't feel the same anymore",
                                               id=uuid.UUID('aed2a29a-2d9d-4f5e-8539-73588b774101'),
                                               act=2, percentage=77, enabled=False),
                                     StoryBeat(text='Dark Night of the Soul',
                                               type=StoryBeatType.CONTAINER,
                                               icon='mdi.weather-night',
                                               icon_color='#494368',
                                               id=uuid.UUID('c0e89a87-224d-4b97-b4f5-a2ace08fdadb'),
                                               act=2, percentage=75, percentage_end=80),
                                     StoryBeat(text='Break into Three',
                                               icon='mdi.clock-time-nine-outline',
                                               icon_color='#e85d04',
                                               description='An a-ha moment for the protagonist. They realize that they have to change. They know how to fix their flaws and thus resolve the story.',
                                               id=uuid.UUID('677f83ad-355a-47fb-8ff7-812997bdb23a'),
                                               act=2, ends_act=True, percentage=80),
                                     StoryBeat(text='Finale',
                                               type=StoryBeatType.CONTAINER,
                                               icon='fa5s.flag-checkered',
                                               icon_color='#ff7800',
                                               id=uuid.UUID('10191cac-7786-4e85-9a36-75f99be22b92'),
                                               act=3, percentage=80, percentage_end=99),
                                     StoryBeat(text='Gather the Team',
                                               icon='ri.team-fill',
                                               icon_color='#489fb5',
                                               description='The protagonist might need to make some amends and gather allies.',
                                               id=uuid.UUID('777d81b6-b427-4fc0-ba8d-01cde45eedde'),
                                               act=3, percentage=84),
                                     StoryBeat(text='Execute the Plan',
                                               icon='mdi.format-list-checks',
                                               icon_color='#55a630',
                                               description='The protagonist executes the original plan.',
                                               id=uuid.UUID('b99012a6-8c41-43c8-845d-7595ce7140d9'),
                                               act=3, percentage=86),
                                     StoryBeat(text='High Tower Surprise',
                                               icon='mdi.lighthouse-on',
                                               icon_color='#586f7c',
                                               description='A sudden twist! The original plan did not work out.',
                                               id=uuid.UUID('fe77f4f2-9064-4b06-8062-920635aa415c'),
                                               act=3, percentage=88),
                                     StoryBeat(text='Dig Deep Down',
                                               icon='mdi.shovel',
                                               icon_color='#b08968',
                                               description='A new plan is necessary. The protegonist must find the truth and act accordingly.',
                                               id=uuid.UUID('a5c4d0aa-9811-4988-8611-3483b2499732'),
                                               act=3, percentage=90),
                                     StoryBeat(text='Execute a New Plan',
                                               icon='mdi.lightbulb-on',
                                               icon_color='#4361ee',
                                               description='Execute the new plan and likely resolve the conflict.',
                                               id=uuid.UUID('13d535f6-6b3d-4211-ae44-e0fcf3970186'),
                                               act=3, percentage=95),
                                     StoryBeat(text='Final Image',
                                               icon='fa5s.water',
                                               icon_color='#7192be',
                                               description="An 'after' snapshot of the protagonist to often contrast the opening image.",
                                               id=uuid.UUID('12d5ec21-af96-4e51-9c26-06583d830d87'),
                                               act=3, percentage=99),
                                     ])

heros_journey = StoryStructure(title="Hero's Journey",
                               id=uuid.UUID('d19e6f28-c6ed-4496-8f6b-064ab4306f17'),
                               icon='fa5s.mask',
                               beats=[
                                   StoryBeat(text='Ordinary World',
                                             icon='fa5.image',
                                             icon_color='#1ea896',
                                             description='The hero is introduced alongside their ordinary world.',
                                             id=uuid.UUID('99e3f76b-6bbe-44e8-8733-5c9334b3b2ec'),
                                             act=1,
                                             percentage=1),
                                   StoryBeat(text='Call to Adventure',
                                             icon='mdi.bell-alert-outline',
                                             icon_color='#a2ad59',
                                             description='The hero is presented with a challenge or opportunity to embark on a journey',
                                             id=uuid.UUID('e246082a-67ff-412b-9f07-7310339157a5'),
                                             act=1,
                                             percentage=10),
                                   StoryBeat(text='Refusal of the Call',
                                             icon='mdi6.hand-back-left',
                                             icon_color='#e5989b',
                                             description='The hero initially refuses the call to adventure',
                                             id=uuid.UUID('638ff0ec-e867-48a5-a606-54de7e39eeee'),
                                             act=1,
                                             percentage=14),
                                   StoryBeat(text='Meeting with the Mentor',
                                             icon='mdi.compass-rose',
                                             icon_color='#80ced7',
                                             description='The hero meets their mentor who will offer guidance or tools necessary to succeed with the journey',
                                             id=uuid.UUID('c3b899f2-c6c4-4306-98e7-359ab65851be'),
                                             act=1,
                                             percentage=18),
                                   StoryBeat(text='Crossing the First Threshold',
                                             icon='fa5s.torii-gate',
                                             icon_color='#a4161a',
                                             description='The hero leaves the ordinary world and embarks on the journey',
                                             id=uuid.UUID('f4e9b677-bfc2-443f-b4b3-0691e398b3d5'),
                                             act=1,
                                             ends_act=True,
                                             percentage=25),
                                   StoryBeat(text='Tests, Allies, Enemies',
                                             type=StoryBeatType.CONTAINER,
                                             icon='ph.users-three-fill',
                                             icon_color='#947eb0',
                                             description='The hero faces trials and battles, makes allies and enemies along the way',
                                             id=uuid.UUID('e4392aeb-a8a6-453c-ab3d-57eb3a33d230'),
                                             act=2,
                                             percentage=25, percentage_end=45),
                                   StoryBeat(text='Approach to the Inmost Cave',
                                             icon='mdi6.tunnel-outline',
                                             icon_color='#7f4f24',
                                             description='The hero reaches a dangerous and crucial point of their journey',
                                             id=uuid.UUID('301b1121-9d98-41cd-b41c-75af1396e63d'),
                                             act=2,
                                             percentage=40),
                                   StoryBeat(text='Ordeal',
                                             icon='mdi6.skull',
                                             description='The hero faces a decisive challenge and fails, having an all-time low moment, but only to be reborn later',
                                             id=uuid.UUID('46cfccac-f5fe-463c-8f4b-5075b9b5e733'),
                                             act=2,
                                             percentage=50),
                                   StoryBeat(text='Reward',
                                             icon='mdi6.flask-round-bottom',
                                             icon_color='#414833',
                                             description='The hero achieves the goal of the journey and receives a reward',
                                             id=uuid.UUID('6e14dba8-86ce-48c6-8324-5eda18d73ecc'),
                                             act=2,
                                             percentage=60),
                                   StoryBeat(text='The Road Back',
                                             icon='fa5s.route',
                                             icon_color='#0077b6',
                                             description='The hero returns to the ordinary world, often with a newfound understanding or power',
                                             id=uuid.UUID('2f7b08de-04dc-401b-ba72-b30f8dbfe74f'),
                                             act=2,
                                             ends_act=True,
                                             percentage=75),
                                   StoryBeat(text='Resurrection',
                                             icon='fa5s.chevron-up',
                                             icon_color='#ce2d4f',
                                             description='The hero must confront and overcome a final challenge, often a reflection of the initial challenge ending with another death and rebirth',
                                             id=uuid.UUID('7013dc29-ac7d-47df-893d-95211f15fd77'),
                                             act=3,
                                             percentage=90),
                                   StoryBeat(text='Return with the Elixir',
                                             icon='mdi6.flask-round-bottom-empty',
                                             icon_color='#023e8a',
                                             description='The hero returns to the ordinary world with the reward and applies what they have learned to their life',
                                             id=uuid.UUID('ca7da757-31fa-4ffb-902d-b7c391bb9bc3'),
                                             act=3,
                                             percentage=98)
                               ]
                               )

default_story_structures = [three_act_structure, save_the_cat, heros_journey]


@dataclass
class LanguageSettings:
    lang: str = 'en-US'


class ImportOriginType(Enum):
    SCRIVENER = 'scrivener'


@dataclass
class ImportOrigin:
    type: ImportOriginType
    source: str
    source_id: Optional[uuid.UUID] = None
    sync: bool = False
    last_mod_time: int = 0


@dataclass
class NovelDescriptor:
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    lang_settings: LanguageSettings = field(default_factory=LanguageSettings)
    import_origin: Optional[ImportOrigin] = None
    subtitle: str = field(default='', metadata=config(exclude=exclude_if_empty))
    icon: str = field(default='', metadata=config(exclude=exclude_if_empty))
    icon_color: str = field(default='black', metadata=config(exclude=exclude_if_black))
    tutorial: bool = False
    creation_date: Optional[datetime] = None

    def __post_init__(self):
        if self.creation_date is None:
            self.creation_date = datetime.now()

    @overrides
    def __eq__(self, other: 'NovelDescriptor'):
        if isinstance(other, NovelDescriptor):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))

    def is_scrivener_sync(self) -> bool:
        if self.import_origin is None:
            return False
        return self.import_origin.type == ImportOriginType.SCRIVENER and self.import_origin.sync

    def is_readonly(self) -> bool:
        if self.import_origin is None:
            return False
        return self.import_origin.sync


@dataclass
class CausalityItem(SelectionItem):
    links: List['CausalityItem'] = field(default_factory=list)

    @overrides
    def __eq__(self, other: 'CausalityItem'):
        if isinstance(other, CausalityItem):
            return self.text == other.text
        return False

    @overrides
    def __hash__(self):
        return hash(self.text)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Causality:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    items: List['CausalityItem'] = field(default_factory=list)


class MiceType(Enum):
    CHARACTER = 0
    INQUIRY = 1
    MILIEU = 2
    EVENT = 3


@dataclass
class MiceThread:
    type: MiceType
    text: str = ''
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    beginning_scene_id: Optional[uuid.UUID] = field(default=None, metadata=config(exclude=exclude_if_empty))
    ending_scene_id: Optional[uuid.UUID] = field(default=None, metadata=config(exclude=exclude_if_empty))

    def beginning_scene(self, novel: 'Novel') -> Optional['Scene']:
        if not self.beginning_scene_id:
            return None
        for s in novel.scenes:
            if s.id == self.beginning_scene_id:
                return s

    def ending_scene(self, novel: 'Novel') -> Optional['Scene']:
        if not self.ending_scene_id:
            return None
        for s in novel.scenes:
            if s.id == self.ending_scene_id:
                return s


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MiceQuotient:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    threads: List[MiceThread] = field(default_factory=list)


class DocumentType(Enum):
    DOCUMENT = 0
    CHARACTER_BACKSTORY = 1
    CAUSE_AND_EFFECT = 2
    REVERSED_CAUSE_AND_EFFECT = 3
    SNOWFLAKE = 4
    CHARACTER_ARC = 5
    STORY_STRUCTURE = 6
    MICE = 7


@dataclass
class TextStatistics:
    word_count: int = -1


@dataclass
class DocumentStatistics:
    wc: int = 0


@dataclass
class Document(CharacterBased, SceneBased):
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    type: DocumentType = DocumentType.DOCUMENT
    children: List['Document'] = field(default_factory=list)
    character_id: Optional[uuid.UUID] = field(default=None, metadata=config(exclude=exclude_if_empty))
    scene_id: Optional[uuid.UUID] = field(default=None, metadata=config(exclude=exclude_if_empty))
    data_id: Optional[uuid.UUID] = field(default=None, metadata=config(exclude=exclude_if_empty))
    icon: str = field(default='', metadata=config(exclude=exclude_if_empty))
    icon_color: str = field(default='black', metadata=config(exclude=exclude_if_black))
    statistics: Optional[DocumentStatistics] = field(default=None, metadata=config(exclude=exclude_if_empty))

    @overrides
    def __eq__(self, other: 'Document'):
        if isinstance(other, Document):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))

    def __post_init__(self):
        self.loaded: bool = False
        self.content: str = ''
        self.data: Any = None
        self._character: Optional[Character] = None
        self._scene: Optional[Scene] = None


def default_documents() -> List[Document]:
    return [Document('Story', id=uuid.UUID('ec2a62d9-fc00-41dd-8a6c-b121156b6cf4'), icon='fa5s.book-open'),
            Document('Characters', id=uuid.UUID('8fa16650-bed0-489b-baa1-d239e5198d47'), icon='fa5s.user'),
            Document('Scenes', id=uuid.UUID('75a552f4-037d-4179-860f-dd8400a7545b'), icon='mdi.movie-open'),
            Document('Worldbuilding', id=uuid.UUID('5faf7c16-f970-465d-bbcb-1bad56f3313c'), icon='mdi.globe-model')]


@dataclass
class TagType(SelectionItem):
    description: str = ''

    @overrides
    def __eq__(self, other: 'TagType'):
        if isinstance(other, TagType):
            return self.text == other.text
        return False

    @overrides
    def __hash__(self):
        return hash(self.text)


@dataclass
class Tag(SelectionItem):
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    tag_type: str = 'General'
    builtin: bool = False

    @overrides
    def __eq__(self, other: 'Tag'):
        if isinstance(other, Tag):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


def default_general_tags() -> List[Tag]:
    return [
        Tag('Flashback', id=uuid.UUID('1daadfcf-dc6a-4b9d-b708-f9577cbb9e83'), icon='fa5s.backward', icon_color='white',
            color_hexa='#1b263b', builtin=True),
        Tag('Flashforward', id=uuid.UUID('a5db2d5f-099d-4d01-83e8-31c726f04100'), icon='fa5s.forward',
            icon_color='white',
            color_hexa='#1b998b', builtin=True),
        Tag('Ticking clock', id=uuid.UUID('88ab7b73-6934-4f63-8022-0b8732caa8bd'), icon='mdi.clock-alert-outline',
            icon_color='#f7cb15', builtin=True),
        Tag('Foreshadowing', id=uuid.UUID('2ba0c868-da0f-44fc-9142-fef0bfa6e1c6'), icon='mdi.crystal-ball',
            icon_color='#76bed0', builtin=True),
        Tag('Cliffhanger', id=uuid.UUID('51e0bcc5-396e-4602-b195-fc8efe985f13'), icon='mdi.target-account',
            icon_color='#f7cb15', builtin=True),
        Tag('Backstory', id=uuid.UUID('72d155da-df20-4b64-84d3-acfbbc7f87c7'), icon='mdi.archive', icon_color='#9a6d38',
            builtin=True),
        Tag('Red herring', id=uuid.UUID('96ff9491-cdd3-4c85-8086-ee47144828cb'), icon='fa5s.fish', icon_color='#d33f49',
            builtin=True)]


def default_tag_types() -> List[TagType]:
    return [
        TagType('General', icon='ei.tags', icon_color='#2a2a72',
                description='General tags that can be tracked for each scene.'),
        TagType('Symbols', icon='fa5s.dove', icon_color='#5995ed',
                description='A symbol can be anything that represents something beyond their literal meaning.'),
        TagType('Motifs', icon='mdi6.glass-fragile', icon_color='#8ac6d0',
                description='A motif is a recurring object, sound, situation, phrase, or idea throughout the story'
                            + ' that empowers the theme.'),
        TagType('Items', icon='mdi.ring', icon_color='#b6a6ca',
                description='Relevant items that reappear throughout the story.'
                            + ' They do not have symbolic meaning unlike Symbols or Motifs.'),
        # TagType('Themes', icon='ei.idea-alt', icon_color='#f72585',
        #         description='The main ideas or lessons that the story explores.')
    ]


def default_tags() -> Dict[TagType, List[Tag]]:
    tags = {}
    types = default_tag_types()
    for t in types:
        if t.text == 'General':
            tags[t] = default_general_tags()
        else:
            tags[t] = []

    return tags


class DiagramNodeType(Enum):
    CHARACTER = 'character'
    STICKER = 'sticker'
    EVENT = 'event'
    COMMENT = 'comment'
    SETUP = 'setup'


NODE_SUBTYPE_GOAL = 'goal'
NODE_SUBTYPE_CONFLICT = 'conflict'
NODE_SUBTYPE_DISTURBANCE = 'disturbance'
NODE_SUBTYPE_BACKSTORY = 'backstory'
NODE_SUBTYPE_INTERNAL_CONFLICT = 'internal_conflict'
NODE_SUBTYPE_QUESTION = 'question'
NODE_SUBTYPE_FORESHADOWING = 'foreshadowing'
NODE_SUBTYPE_TOOL = 'tool'
NODE_SUBTYPE_COST = 'cost'


@dataclass
class Node(CharacterBased):
    x: float
    y: float
    type: DiagramNodeType
    subtype: str = field(default='', metadata=config(exclude=exclude_if_empty))
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    character_id: Optional[uuid.UUID] = field(default=None, metadata=config(exclude=exclude_if_empty))
    icon: str = field(default='', metadata=config(exclude=exclude_if_empty))
    color: str = field(default='black', metadata=config(exclude=exclude_if_black))
    text: str = field(default='', metadata=config(exclude=exclude_if_empty))
    size: int = 12
    bold: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    italic: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    underline: bool = field(default=False, metadata=config(exclude=exclude_if_false))

    def __post_init__(self):
        self._character: Optional[Character] = None


def to_node(x: float, y: float, type: DiagramNodeType, subtype: str = '', default_size: int = 12) -> Node:
    node = Node(x, y, type=type, subtype=subtype)
    if type == DiagramNodeType.EVENT:
        node.size = max(20 if app_env.is_mac() else 16, default_size)
        if subtype in [NODE_SUBTYPE_BACKSTORY, NODE_SUBTYPE_INTERNAL_CONFLICT]:
            node.size = max(16 if app_env.is_mac() else 14, default_size - 1)

    if subtype == NODE_SUBTYPE_GOAL:
        node.icon = 'mdi.target'
        node.color = 'darkBlue'
    elif subtype == NODE_SUBTYPE_CONFLICT:
        node.icon = 'mdi.sword-cross'
        node.color = '#f3a712'
    elif subtype == NODE_SUBTYPE_BACKSTORY:
        node.icon = 'fa5s.archive'
        node.color = '#9c6644'
    elif subtype == NODE_SUBTYPE_INTERNAL_CONFLICT:
        node.icon = 'mdi.mirror'
        node.color = '#94b0da'
    elif subtype == NODE_SUBTYPE_DISTURBANCE:
        node.icon = 'mdi.bell-alert-outline'
        node.color = '#a2ad59'
    elif subtype == NODE_SUBTYPE_QUESTION:
        node.icon = 'ei.question-sign'
    elif subtype == NODE_SUBTYPE_FORESHADOWING:
        node.icon = 'mdi6.crystal-ball'

    return node


@dataclass
class Connector:
    source_id: uuid.UUID
    target_id: uuid.UUID
    source_angle: float
    target_angle: float
    type: str = ''
    pen: Qt.PenStyle = Qt.PenStyle.SolidLine
    width: int = 1
    icon: str = field(default='', metadata=config(exclude=exclude_if_empty))
    color: str = field(default='black', metadata=config(exclude=exclude_if_black))
    text: str = field(default='', metadata=config(exclude=exclude_if_empty))


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DiagramData:
    nodes: List[Node] = field(default_factory=list)
    connectors: List[Connector] = field(default_factory=list)


@dataclass
class Diagram:
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    icon: str = field(default='', metadata=config(exclude=exclude_if_empty))
    icon_color: str = field(default='black', metadata=config(exclude=exclude_if_black))

    def __post_init__(self):
        self.loaded: bool = False
        self.data: Optional[DiagramData] = None

    @overrides
    def __eq__(self, other: 'Diagram'):
        if isinstance(other, Diagram):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))


def default_events_map() -> Diagram:
    return Diagram('Events', id=uuid.UUID('6c74e40f-d3de-4c83-bcd2-0ca5e626081d'))


def default_character_networks() -> List[Diagram]:
    return [Diagram('Character relations', id=uuid.UUID('bfd1f2d3-cb33-48a6-a09e-b4332c3d1ed1'))]


@dataclass
class Relation(SelectionItem):
    pass


@dataclass
class DocsPreferences:
    grammar_check: bool = True


class NovelPanel(Enum):
    OUTLINE = 'outline'
    MANUSCRIPT = 'manuscript'
    REPORTS = 'reports'


class ScenesView(Enum):
    NOVEL = 'novel'
    CHARACTERS = 'characters'
    SCENES = 'scenes'
    WORLD_BUILDING = 'world_building'
    DOCS = 'docs'
    MANUSCRIPT = 'manuscript'
    BOARD = 'board'
    REPORTS = 'reports'


@dataclass
class PanelPreferences:
    panel: NovelPanel = NovelPanel.OUTLINE
    scenes_view: Optional[ScenesView] = None
    scene_chapters_sidebar_toggled: bool = False


class NovelSetting(Enum):
    Structure = 'structure'
    Storylines = 'storylines'
    Mindmap = 'mindmap'
    Characters = 'characters'
    Scenes = 'scenes'
    Track_emotion = 'track_emotion'
    Track_conflict = 'track_conflict'
    Documents = 'documents'
    Manuscript = 'manuscript'
    World_building = 'world_building'
    Management = 'management'


@dataclass
class NovelPreferences:
    active_stage_id: Optional[uuid.UUID] = None
    docs: DocsPreferences = field(default_factory=DocsPreferences)
    panels: PanelPreferences = field(default_factory=PanelPreferences)
    settings: Dict[str, Any] = field(default_factory=dict)

    def toggled(self, setting: NovelSetting) -> bool:
        return self.settings.get(setting.value, True)


@dataclass
class ManuscriptGoals:
    target_wc: int = 80000


@dataclass
class Novel(NovelDescriptor):
    story_structures: List[StoryStructure] = field(default_factory=list)
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
    plots: List[Plot] = field(default_factory=list)
    chapters: List[Chapter] = field(default_factory=list)
    custom_chapters: int = field(default=0, metadata=config(exclude=exclude_if_empty))
    stages: List[SceneStage] = field(default_factory=default_stages)
    character_profiles: List[ProfileTemplate] = field(default_factory=default_character_profiles)
    character_topics: List[Topic] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)
    goals: List[Goal] = field(default_factory=list)
    documents: List[Document] = field(default_factory=default_documents)
    tags: Dict[TagType, List[Tag]] = field(default_factory=default_tags)
    premise: str = ''
    synopsis: Optional['Document'] = None
    prefs: NovelPreferences = field(default_factory=NovelPreferences)
    world: WorldBuilding = field(default_factory=WorldBuilding)
    board: Board = field(default_factory=Board)
    manuscript_goals: ManuscriptGoals = field(default_factory=ManuscriptGoals)
    events_map: Diagram = field(default_factory=default_events_map)
    character_networks: List[Diagram] = field(default_factory=default_character_networks)

    def pov_characters(self) -> List[Character]:
        pov_ids = set()
        povs: List[Character] = []
        for scene in self.scenes:
            if scene.pov and str(scene.pov.id) not in pov_ids:
                povs.append(scene.pov)
                pov_ids.add(str(scene.pov.id))

        return povs

    def agenda_characters(self) -> List[Character]:
        char_ids = set()
        chars: List[Character] = []
        for scene in self.scenes:
            for agenda in scene.agendas:
                if agenda.character_id and str(agenda.character_id) not in char_ids:
                    character: Character = agenda.character(self)
                    if character:
                        chars.append(character)
                        char_ids.add(str(character.id))

        return chars

    def major_characters(self) -> List[Character]:
        return [x for x in self.characters if x.is_major()]

    def secondary_characters(self) -> List[Character]:
        return [x for x in self.characters if x.is_secondary()]

    def minor_characters(self) -> List[Character]:
        return [x for x in self.characters if x.is_minor()]

    @property
    def active_story_structure(self) -> StoryStructure:
        for structure in self.story_structures:
            if structure.active:
                return structure
        return self.story_structures[0]

    @property
    def active_stage(self) -> Optional[SceneStage]:
        if self.prefs.active_stage_id:
            for stage in self.stages:
                if stage.id == self.prefs.active_stage_id:
                    return stage

    def scenes_in_chapter(self, chapter: Chapter) -> List[Scene]:
        return [x for x in self.scenes if x.chapter is chapter]

    @staticmethod
    def new_scene(title: str = '') -> Scene:
        return Scene(title, agendas=[SceneStructureAgenda()])

    @staticmethod
    def new_novel(title: str = '') -> 'Novel':
        novel = Novel(title)
        novel.story_structures = [copy.deepcopy(three_act_structure)]
        return novel

    def insert_scene_after(self, scene: Scene, chapter: Optional[Chapter] = None) -> Scene:
        i = self.scenes.index(scene)
        day = scene.day

        new_scene = self.new_scene()
        new_scene.day = day
        if chapter:
            new_scene.chapter = chapter
        else:
            new_scene.chapter = scene.chapter
        self.scenes.insert(i + 1, new_scene)

        return new_scene

    def update_chapter_titles(self):
        i = 1
        for chapter in self.chapters:
            if chapter.type is None:
                chapter.title = f'Chapter {i}'
                i += 1

    @overrides
    def __eq__(self, other: 'Novel'):
        if isinstance(other, Novel):
            return self.id == other.id
        return False

    @overrides
    def __hash__(self):
        return hash(str(self.id))
