"""
Plotlyst
Copyright (C) 2021-2022  Zsolt Kovari

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
from typing import List, Any, Dict, Optional

from PyQt6.QtCore import Qt
from dataclasses_json import config
from overrides import overrides


def exclude_if_empty(value):
    return not value


def exclude_if_true(value):
    return value is True


def exclude_if_false(value):
    return value is False


def exclude_if_black(value):
    return value == 'black'


class SelectionItemType(Enum):
    CHOICE = 0
    SEPARATOR = 1


def exclude_if_choice(value):
    return value == SelectionItemType.CHOICE


@dataclass
class SelectionItem:
    text: str
    type: SelectionItemType = field(default=SelectionItemType.CHOICE, metadata=config(exclude=exclude_if_choice))
    icon: str = field(default='', metadata=config(exclude=exclude_if_empty))
    icon_color: str = field(default='black', metadata=config(exclude=exclude_if_black))
    color_hexa: str = field(default='', metadata=config(exclude=exclude_if_empty))
    meta: Dict[str, Any] = field(default_factory=dict, metadata=config(exclude=exclude_if_empty))

    @overrides
    def __hash__(self):
        return hash(self.text)


class TemplateFieldType(Enum):
    TEXT = 0
    SMALL_TEXT = 1
    TEXT_SELECTION = 2
    BUTTON_SELECTION = 3
    NUMERIC = 4
    IMAGE = 5
    LABELS = 6
    DISPLAY_SUBTITLE = 7
    DISPLAY_LABEL = 8
    DISPLAY_LINE = 9
    DISPLAY_HEADER = 10
    DISPLAY_ICON = 11


class SelectionType(Enum):
    SINGLE_LIST = 0
    CHECKBOX = 1
    CHECKED_BUTTON = 2
    TAGS = 3


@dataclass
class TemplateField:
    name: str
    type: TemplateFieldType
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    description: str = field(default='', metadata=config(exclude=exclude_if_empty))
    emoji: str = field(default='', metadata=config(exclude=exclude_if_empty))
    placeholder: str = field(default='', metadata=config(exclude=exclude_if_empty))
    selections: List[SelectionItem] = field(default_factory=list)
    required: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    exclusive: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    enabled: bool = field(default=True, metadata=config(exclude=exclude_if_true))
    custom: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    min_value: int = field(default=0, metadata=config(exclude=exclude_if_empty))
    max_value = 2_147_483_647
    compact: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    show_label: bool = field(default=True, metadata=config(exclude=exclude_if_true))
    color: str = field(default='', metadata=config(exclude=exclude_if_empty))
    has_notes: bool = field(default=False, metadata=config(exclude=exclude_if_false))

    @overrides
    def __hash__(self):
        return hash(str(self.id))


age_field = TemplateField(name='Age', type=TemplateFieldType.NUMERIC,
                          id=uuid.UUID('7c8fccb8-9228-495a-8edd-3f991ebeed4b'), emoji=':birthday_cake:',
                          show_label=False, compact=True, placeholder='Age')

enneagram_field = TemplateField(name='Enneagram', type=TemplateFieldType.TEXT_SELECTION,
                                id=uuid.UUID('be281490-c1b7-413c-b519-f780dbdafaeb'),
                                selections=[SelectionItem('Perfectionist', icon='mdi.numeric-1-circle',
                                                          icon_color='#1f487e',
                                                          meta={'positive': ['Rational', 'Principled', 'Objective',
                                                                             'Structured'],
                                                                'negative': ['Strict'],
                                                                'desire': 'Being good, balanced, have integrity',
                                                                'fear': 'Being incorrect, corrupt, evil',
                                                                'number': 1}),
                                            SelectionItem('Giver', icon='mdi.numeric-2-circle',
                                                          icon_color='#7ae7c7',
                                                          meta={'positive': ['Generous', 'Warm', 'Caring'],
                                                                'negative': ['Possessive'],
                                                                'desire': 'To be loved and appreciated',
                                                                'fear': 'Being unloved, unwanted',
                                                                'number': 2}
                                                          ),
                                            SelectionItem('Achiever', icon='mdi.numeric-3-circle',
                                                          icon_color='#297045',
                                                          meta={'positive': ['Pragmatic', 'Driven', 'Ambitious'],
                                                                'negative': ['Image-conscious'],
                                                                'desire': 'Be valuable and worthwhile',
                                                                'fear': 'Being worthless',
                                                                'number': 3}
                                                          ),
                                            SelectionItem('Individualist', icon='mdi.numeric-4-circle',
                                                          icon_color='#4d8b31',
                                                          meta={'positive': ['Self-aware', 'Sensitive', 'Expressive'],
                                                                'negative': ['Temperamental'],
                                                                'desire': 'Express their individuality',
                                                                'fear': 'Having no identity or significance',
                                                                'number': 4}
                                                          ),
                                            SelectionItem('Investigator', icon='mdi.numeric-5-circle',
                                                          icon_color='#ffc600',
                                                          meta={'positive': ['Perceptive', 'Curious', 'Innovative'],
                                                                'negative': ['Isolated'],
                                                                'desire': 'Be competent',
                                                                'fear': 'Being useless, incompetent',
                                                                'number': 5}
                                                          ),
                                            SelectionItem('Skeptic', icon='mdi.numeric-6-circle',
                                                          icon_color='#ff6b35',
                                                          meta={'positive': ['Committed', 'Responsible', 'Organized'],
                                                                'negative': ['Anxious'],
                                                                'desire': 'Have security and support',
                                                                'fear': 'Being vulnerable and unprepared',
                                                                'number': 6}
                                                          ),
                                            SelectionItem('Enthusiast', icon='mdi.numeric-7-circle',
                                                          icon_color='#ec0b43',
                                                          meta={'positive': ['Optimistic', 'Flexible', 'Practical',
                                                                             'Adventurous'],
                                                                'negative': ['Impulsive', 'Self-centered'],
                                                                'desire': 'Be stimulated, engaged, satisfied',
                                                                'fear': 'Being deprived',
                                                                'number': 7}
                                                          ),
                                            SelectionItem('Challenger', icon='mdi.numeric-8-circle',
                                                          icon_color='#4f0147',
                                                          meta={'positive': ['Decisive', 'Powerful', 'Assertive',
                                                                             'Independent'],
                                                                'negative': ['Confrontational'],
                                                                'desire': 'Be independent and in control',
                                                                'fear': 'Being vulnerable, controlled, harmed',
                                                                'number': 8}
                                                          ),
                                            SelectionItem('Peacemaker', icon='mdi.numeric-9-circle',
                                                          icon_color='#3a015c',
                                                          meta={'positive': ['Easygoing', 'Understanding', 'Patient',
                                                                             'Supportive'],
                                                                'negative': ['Lazy', 'Indecisive'],
                                                                'desire': 'Internal peace, harmony',
                                                                'fear': 'Loss, separation',
                                                                'number': 9}
                                                          )],
                                compact=True, show_label=False)
mbti_field = TemplateField(name='MBTI', type=TemplateFieldType.TEXT_SELECTION,
                           id=uuid.UUID('bc5408a4-c2bd-4370-b46b-95f20018af01'),
                           selections=[SelectionItem('ISTJ', icon='mdi.magnify', icon_color='#2a9d8f'),  # green
                                       SelectionItem('ISFJ', icon='mdi.fireplace', icon_color='#2a9d8f'),
                                       SelectionItem('ESTP', icon='ei.fire', icon_color='#2a9d8f'),
                                       SelectionItem('ESFP', icon='mdi.microphone-variant', icon_color='#2a9d8f'),

                                       SelectionItem('INFJ', icon='ph.tree-fill', icon_color='#e9c46a'),  # yellow
                                       SelectionItem('INTJ', icon='fa5s.drafting-compass', icon_color='#e9c46a'),
                                       SelectionItem('ENFP', icon='fa5.sun', icon_color='#e9c46a'),
                                       SelectionItem('ENTP', icon='fa5.lightbulb', icon_color='#e9c46a'),

                                       SelectionItem('ISTP', icon='fa5s.hammer', icon_color='#457b9d'),  # blue
                                       SelectionItem('INTP', icon='ei.puzzle', icon_color='#457b9d'),
                                       SelectionItem('ESTJ', icon='mdi.gavel', icon_color='#457b9d'),
                                       SelectionItem('ENTJ', icon='fa5.compass', icon_color='#457b9d'),

                                       SelectionItem('ISFP', icon='mdi6.violin', icon_color='#d00000'),  # red
                                       SelectionItem('INFP', icon='fa5s.cloud-sun', icon_color='#d00000'),
                                       SelectionItem('ESFJ', icon='mdi6.cupcake', icon_color='#d00000'),
                                       SelectionItem('ENFJ', icon='mdi6.flower', icon_color='#d00000'),
                                       ],
                           compact=True, show_label=False)
positive_traits = sorted([
    'Accessible', 'Active', 'Adaptive', 'Admirable', 'Adventurous', 'Agreeable', 'Alert', 'Ambitious', 'Appreciative',
    'Articulate', 'Aspiring', 'Assertive', 'Attentive', 'Balanced', 'Benevolent', 'Calm', 'Capable', 'Captivating',
    'Caring', 'Challenging', 'Charismatic', 'Charming', 'Cheerful', 'Clever', 'Colorful', 'Committed', 'Compassionate',
    'Confident', 'Considerate', 'Cooperative', 'Courageous', 'Creative', 'Curious', 'Daring', 'Decent', 'Decisive',
    'Dedicated', 'Dignified', 'Disciplined', 'Discreet', 'Driven', 'Dutiful', 'Dynamic', 'Earnest', 'Easygoing',
    'Educated', 'Efficient', 'Elegant', 'Empathetic', 'Encouraging', 'Energetic', 'Enthusiastic', 'Expressive', 'Fair',
    'Faithful', 'Flexible', 'Focused', 'Forgiving', 'Friendly', 'Gallant', 'Generous', 'Gentle', 'Genuine', 'Gracious',
    'Hard-working', 'Healthy', 'Hearty', 'Helpful', 'Honest', 'Honorable', 'Humble', 'Humorous', 'Idealistic',
    'Imaginative', 'Impressive', 'Incorruptible', 'Independent', 'Individualistic', 'Innovative', 'Insightful',
    'Intelligent', 'Intuitive', 'Invulnerable', 'Just', 'Kind', 'Knowledge', 'Leaderly', 'Logical', 'Lovable', 'Loyal',
    'Mature', 'Methodical', 'Maticulous', 'Moderate', 'Modest', 'Neat', 'Objective', 'Observant', 'Open', 'Optimistic',
    'Orderly', 'Organized', 'Original', 'Passionate', 'Patient', 'Peaceful', 'Perceptive', 'Perfectionist',
    'Persuasive', 'Playful', 'Popular', 'Powerful', 'Practical', 'Precise', 'Principled', 'Protective', 'Punctual',
    'Purposeful', 'Rational', 'Realistic', 'Reflective', 'Relaxed', 'Reliable', 'Resourceful', 'Respectful',
    'Responsible', 'Responsive', 'Romantic', 'Sane', 'Scholarly', 'Secure', 'Selfless', 'Self-aware', 'Self-critical',
    'Sensitive', 'Sentimental', 'Serious', 'Sharing', 'Skillful', 'Sociable', 'Solid', 'Sophisticated', 'Spontaneous',
    'Structured', 'Supportive', 'Sweet', 'Sympathetic', 'Systematic', 'Tolerant', 'Truthful', 'Trustworthy',
    'Understanding', 'Unselfish', 'Warm', 'Wise', 'Witty', 'Youthful', 'Zany'
])

negative_traits = sorted([
    'Abrasive', 'Abrupt', 'Aimless', 'Aloof', 'Amoral', 'Angry', 'Anxious', 'Apathetic', 'Argumentative', 'Arrogant',
    'Artificial', 'Asocial', 'Assertive', 'Bewildered', 'Bizarre', 'Bland', 'Blunt', 'Brutal', 'Calculating', 'Callous',
    'Careless', 'Cautious', 'Charmless', 'Childish', 'Clumsy', 'Cold', 'Colorless', 'Compulsive', 'Confused',
    'Conventional', 'Confrontational', 'Cowardly', 'Crazy', 'Critical', 'Crude', 'Cruel', 'Cynical', 'Deceitful',
    'Demanding', 'Dependent', 'Desperate', 'Destructive', 'Devious', 'Difficult', 'Discouraging', 'Dishonest',
    'Disloyal', 'Disobedient', 'Disorderly', 'Disorganized', 'Disrespectful', 'Disruptive', 'Disturbing', 'Dull',
    'Egocentric', 'Envious', 'Erratic', 'Extravagant', 'Extreme', 'Faithless', 'False', 'Fanatical', 'Fearful',
    'Flamboyant', 'Foolish', 'Forgetful', 'Fraudulent', 'Frightening', 'Frivolous', 'Gloomy', 'Greedy', 'Grim',
    'Hateful', 'Hesitant', 'Ignorant', 'Ill-mannered', 'Image-conscious', 'Impatient', 'Impractical', 'Imprudent',
    'Impulsive', 'Inconsiderate', 'Incurious', 'Indecisive', 'Indulgent', 'Insecure', 'Insensitive', 'Insincere',
    'Insulting', 'Intolerant', 'Irrational', 'Irresponsible', 'Irritable', 'Isolated', 'Jealous', 'Judgmental', 'Lazy',
    'Malicious', 'Mannered', 'Mean', 'Moody', 'Naive', 'Narcissistic', 'Narrow-minded', 'Negative', 'Neglectful',
    'Nihilistic', 'Obsessive', 'One-dimensional', 'Opinionated', 'Oppressed', 'Outrageous', 'Paranoid', 'Passive',
    'Pompous', 'Possessive', 'Prejudiced', 'Pretentious', 'Procrastinating', 'Quirky', 'Regretful', 'Repressed',
    'Resentful', 'Ridiculous', 'Rigid', 'Rude', 'Sadistic', 'Scheming', 'Scornful', 'Selfish', 'Self-centered',
    'Shortsighted', 'Shy', 'Silly', 'Single-minded', 'Sloppy', 'Slow', 'Sly', 'Small-thinking', 'Strict', 'Stupid',
    'Submissive', 'Superficial', 'Superstitious', 'Suspicious', 'Tasteless', 'Temperamental', 'Tense', 'Thoughtless',
    'Timid', 'Transparent', 'Treacherous', 'Troublesome', 'Unconvincing', 'Uncooperative', 'Uncreative', 'Uncritical',
    'Undisciplined', 'Unfriendly', 'Ungrateful', 'Unhealthy', 'Unimaginative', 'Unimpressive', 'Unlovable',
    'Unrealistic', 'Unreliable', 'Unstable', 'Vulnerable', 'Weak',
])

traits_field = TemplateField(name='Traits', type=TemplateFieldType.LABELS, emoji=':dna:',
                             id=uuid.UUID('76faae5f-b1e4-47f4-9e3f-ed8497f6c6d3'))
for trait in positive_traits:
    traits_field.selections.append(SelectionItem(trait, meta={'positive': True}))
for trait in negative_traits:
    traits_field.selections.append(SelectionItem(trait, meta={'positive': False}))


def get_selection_values(field: TemplateField) -> Dict[str, SelectionItem]:
    _choices = {}
    for item in field.selections:
        if item.type != SelectionItemType.CHOICE:
            continue
        _choices[item.text] = item
    return _choices


enneagram_choices = get_selection_values(enneagram_field)
mbti_choices = get_selection_values(mbti_field)

summary_field = TemplateField('Summary', type=TemplateFieldType.SMALL_TEXT,
                              id=uuid.UUID('90112538-2eca-45e8-81b4-e3c331204e31'),
                              placeholder="Summarize your character's role in the story",
                              show_label=False)

misbelief_field = TemplateField('Misbelief', type=TemplateFieldType.SMALL_TEXT,
                                id=uuid.UUID('32feaa23-acbf-4990-b99f-429747824a0b'),
                                placeholder='The misbelief/lie the character believes in')

desire_field = TemplateField('Conscious desire', type=TemplateFieldType.SMALL_TEXT, emoji=':star-struck:',
                             placeholder='What does the character want in the story?',
                             id=uuid.UUID('eb6626ea-4d07-4b8a-80f0-d92d2fe7f1c3'))

goal_field = TemplateField('External goal', type=TemplateFieldType.SMALL_TEXT, emoji=':bullseye:',
                           placeholder="What external goal does the character want to accomplish?",
                           id=uuid.UUID('99526331-6f3b-429d-ad22-0a4a90ee9d77'), has_notes=True)
internal_goal_field = TemplateField('Internal goal', type=TemplateFieldType.SMALL_TEXT,
                                    emoji=':smiling_face_with_hearts:',
                                    placeholder="What emotional state does the character want to achieve?",
                                    id=uuid.UUID('090d2431-3ae7-4aa3-81b3-2737a8043db7'), has_notes=True)
motivation_field = TemplateField('Motivation', type=TemplateFieldType.SMALL_TEXT, emoji=':right-facing_fist:',
                                 placeholder='Why does the character want to accomplish their goal?',
                                 id=uuid.UUID('5aa2c2e6-90a6-42b2-af7b-b4c82a56390e'), has_notes=True)
internal_motivation_field = TemplateField('Internal motivation', type=TemplateFieldType.SMALL_TEXT, emoji=':red_heart:',
                                          placeholder='Why does the character want to feel that way?',
                                          id=uuid.UUID('6388368e-6d52-4259-b1e2-1d9c1aa5c89d'), has_notes=True)
conflict_field = TemplateField('Conflict', type=TemplateFieldType.SMALL_TEXT, emoji=':crossed_swords:',
                               placeholder='What external force is stopping the character from their goal?',
                               id=uuid.UUID('c7e39f6d-4b94-4060-b3a6-d2604247ca80'), has_notes=True)
internal_conflict_field = TemplateField('Internal conflict', type=TemplateFieldType.SMALL_TEXT, emoji=':fearful_face:',
                                        placeholder='What stops the character from their desired emotional state?',
                                        id=uuid.UUID('8dcf6ce1-6679-4100-b332-8898ee2a2e3c'), has_notes=True)
stakes_field = TemplateField('Stakes', type=TemplateFieldType.SMALL_TEXT, emoji=':skull:',
                             placeholder="What's at stake if the character fails to reach their goal?",
                             id=uuid.UUID('15770e28-b801-44c4-a6e6-ddba33935bc4'), has_notes=True)
internal_stakes_field = TemplateField('Internal stakes', type=TemplateFieldType.SMALL_TEXT, emoji=':broken_heart:',
                                      placeholder="What's at stake if the character fails to achieve that emotional state?",
                                      id=uuid.UUID('95f58293-c77a-4ec7-9e1f-b2f38d123e8d'), has_notes=True)
need_field = TemplateField('Need', type=TemplateFieldType.SMALL_TEXT, emoji=':face_with_monocle:',
                           placeholder='What does the character actually need in the story?',
                           id=uuid.UUID('2adb45eb-5a6f-4958-82f1-f4ae65124322'))
weaknesses_field = TemplateField('Flaws and weaknesses', type=TemplateFieldType.SMALL_TEXT, emoji=':nauseated_face:',
                                 placeholder="What are the character's weaknesses or flaws in the story?",
                                 id=uuid.UUID('f2aa5655-88b2-41ae-a630-c7e56795a858'))
ghost_field = TemplateField('Ghost', type=TemplateFieldType.SMALL_TEXT, emoji=':ghost:',
                            placeholder="What's the character's ghost from their past that haunts them?",
                            id=uuid.UUID("12a61aa5-ffc0-4309-9b65-c6f26ab5bcf5"))
values_field = TemplateField('Values', type=TemplateFieldType.LABELS, emoji=':smiling_face_with_open_hands:',
                             id=uuid.UUID('47e2e30e-1708-414b-be79-3413063a798d'))

values_items = [SelectionItem('Altruism', icon='fa5s.hand-holding-heart'),
                SelectionItem('Authenticity', icon='mdi6.certificate'),
                SelectionItem('Adventure', icon='mdi6.snowboard'),
                SelectionItem('Authority', icon='ri.government-fill'),
                SelectionItem('Autonomy', icon='fa5s.fist-raised'),
                SelectionItem('Balance', icon='fa5s.balance-scale'),
                SelectionItem('Beauty', icon='mdi6.butterfly'), SelectionItem('Bravery', icon='mdi.sword'),
                SelectionItem('Compassion', icon='mdi6.hand-heart'),
                SelectionItem('Citizenship', icon='mdi.passport'), SelectionItem('Community', icon='ei.group-alt'),
                SelectionItem('Competency', icon='fa5s.user-cog'),
                SelectionItem('Contribution', icon='fa5s.hand-holding-usd'),
                SelectionItem('Creativity', icon='mdi.head-lightbulb-outline'),
                SelectionItem('Curiosity', icon='ei.question-sign'),
                SelectionItem('Dignity', icon='fa5.handshake'), SelectionItem('Equality', icon='ri.scales-fill'),
                SelectionItem('Faith', icon='fa5s.hands'),
                SelectionItem('Fame', icon='ei.star-alt'), SelectionItem('Family', icon='mdi6.human-male-female-child'),
                SelectionItem('Forgiveness', icon='fa5s.hand-peace'),
                SelectionItem('Friendships', icon='fa5s.user-friends'), SelectionItem('Fun', icon='fa5s.football-ball'),
                SelectionItem('Generosity', icon='fa5s.gift'),
                SelectionItem('Growth', icon='fa5s.seedling'),
                SelectionItem('Happiness', icon='mdi.emoticon-happy-outline'),
                SelectionItem('Harmony', icon='mdi6.yin-yang'),
                SelectionItem('Honesty', icon='mdi.mother-heart'),
                SelectionItem('Honour', icon='fa5s.award'), SelectionItem('Humor', icon='fa5.laugh-squint'),
                SelectionItem('Independence', icon='fa.chain-broken'),
                SelectionItem('Integrity', icon='mdi.shield-link-variant'), SelectionItem('Justice', icon='mdi.gavel'),
                SelectionItem('Kindness', icon='mdi.balloon'),
                SelectionItem('Knowledge', icon='fa5s.book'),
                SelectionItem('Leadership', icon='fa5b.font-awesome-flag'),
                SelectionItem('Learning', icon='mdi6.book-education-outline'),
                SelectionItem('Love', icon='fa5s.heart'), SelectionItem('Loyalty', icon='fa5s.dog'),
                SelectionItem('Nature', icon='mdi.tree'),
                SelectionItem('Openness', icon='mdi.lock-open-variant'),
                SelectionItem('Optimism', icon='mdi6.white-balance-sunny'), SelectionItem('Peace', icon='fa5s.dove'),
                SelectionItem('Pleasure', icon='mdi.cupcake'),
                SelectionItem('Popularity', icon='fa5s.thumbs-up'), SelectionItem('Recognition', icon='ri.award-fill'),
                SelectionItem('Religion', icon='fa5s.praying-hands'),
                SelectionItem('Reputation', icon='fa5s.star'), SelectionItem('Respect', icon='ph.handshake-bold'),
                SelectionItem('Responsibility', icon='mdi.cog-clockwise'),
                SelectionItem('Security', icon='mdi.security'), SelectionItem('Service', icon='mdi.room-service'),
                SelectionItem('Spirituality', icon='mdi6.meditation'),
                SelectionItem('Stability', icon='fa.balance-scale'),
                SelectionItem('Success', icon='fa5s.money-bill'),
                SelectionItem('Sustainability', icon='fa5s.leaf'), SelectionItem('Status', icon='mdi6.crown-circle'),
                SelectionItem('Trustworthiness', icon='fa5s.stamp'),
                SelectionItem('Wealth', icon='fa5s.coins'), SelectionItem('Wisdom', icon='mdi.owl')]
values_field.selections.extend(values_items)


class RoleImportance(Enum):
    MAJOR = 0
    SECONDARY = 1
    MINOR = 2


@dataclass
class Role(SelectionItem):
    can_be_promoted: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    promoted: bool = field(default=False, metadata=config(exclude=exclude_if_false))
    importance: RoleImportance = RoleImportance.SECONDARY

    def is_major(self) -> bool:
        return self.importance == RoleImportance.MAJOR or self.promoted

    def is_secondary(self) -> bool:
        return self.importance == RoleImportance.SECONDARY and not self.promoted

    def is_minor(self) -> bool:
        return self.importance == RoleImportance.MINOR


protagonist_role = Role('Protagonist', icon='fa5s.chess-king', icon_color='#00798c', importance=RoleImportance.MAJOR)
deuteragonist_role = Role('Deuteragonist', icon='mdi.atom-variant', icon_color='#820b8a',
                          importance=RoleImportance.MAJOR)
antagonist_role = Role('Antagonist', icon='mdi.guy-fawkes-mask', icon_color='#bc412b', importance=RoleImportance.MAJOR)
contagonist_role = Role('Contagonist', icon='mdi.biohazard', icon_color='#ea9010')
adversary_role = Role('Adversary', icon='fa5s.thumbs-down', icon_color='#9e1946')
guide_role = Role('Guide', icon='mdi.compass-rose', icon_color='#80ced7')
confidant_role = Role('Confidant', icon='fa5s.user-friends', icon_color='#304d6d', can_be_promoted=True)
sidekick_role = Role('Sidekick', icon='ei.asl', icon_color='#b0a990', can_be_promoted=True)
love_interest_role = Role('Love Interest', icon='ei.heart', icon_color='#d1495b', can_be_promoted=True)
supporter_role = Role('Supporter', icon='fa5s.thumbs-up', icon_color='#266dd3')
foil_role = Role('Foil', icon='fa5s.yin-yang', icon_color='#947eb0', can_be_promoted=True)
secondary_role = Role('Secondary', icon='fa5s.chess-knight', icon_color='#619b8a', can_be_promoted=True)
henchmen_role = Role('Heckler', icon='mdi.shuriken', icon_color='#596475', importance=RoleImportance.MINOR)
tertiary_role = Role('Tertiary', icon='mdi.chess-pawn', icon_color='#886f68', importance=RoleImportance.MINOR)


class HAlignment(Enum):
    DEFAULT = 0
    LEFT = Qt.AlignmentFlag.AlignLeft
    RIGHT = Qt.AlignmentFlag.AlignRight
    CENTER = Qt.AlignmentFlag.AlignHCenter
    JUSTIFY = Qt.AlignmentFlag.AlignJustify


class VAlignment(Enum):
    TOP = Qt.AlignmentFlag.AlignTop
    BOTTOM = Qt.AlignmentFlag.AlignBottom
    CENTER = Qt.AlignmentFlag.AlignVCenter


@dataclass
class Margins:
    left: int = 2
    top: int = 0
    right: int = 2
    bottom: int = 0


@dataclass
class ProfileElement:
    field: TemplateField
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    h_alignment: HAlignment = HAlignment.DEFAULT
    v_alignment: VAlignment = VAlignment.TOP
    margins: Optional[Margins] = None


@dataclass
class ProfileTemplate:
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    elements: List[ProfileElement] = field(default_factory=list)


def default_character_profiles() -> List[ProfileTemplate]:
    def arrow_field():
        return TemplateField('ph.arrow-fat-lines-up-fill', type=TemplateFieldType.DISPLAY_ICON, color='darkBlue')

    def internal_arrow_field():
        return TemplateField('ph.arrow-fat-lines-up-fill', type=TemplateFieldType.DISPLAY_ICON, color='#94b0da')

    summary_title = TemplateField('Summary', type=TemplateFieldType.DISPLAY_HEADER, required=True)
    characterization_title = TemplateField('Personality', type=TemplateFieldType.DISPLAY_HEADER, required=True)
    goal_title = TemplateField('Goal', type=TemplateFieldType.DISPLAY_HEADER)
    story_title = TemplateField('Story attributes', type=TemplateFieldType.DISPLAY_HEADER)

    fields = [ProfileElement(summary_title, 0, 0, col_span=2),
              ProfileElement(summary_field, 1, 0, col_span=2, margins=Margins(left=15)),
              ProfileElement(characterization_title, 2, 0, col_span=2),
              ProfileElement(enneagram_field, 3, 0, col_span=2, margins=Margins(left=15)),
              ProfileElement(mbti_field, 4, 0, col_span=2, margins=Margins(left=15)),
              ProfileElement(traits_field, 5, 0, col_span=2, margins=Margins(left=15)),
              ProfileElement(goal_title, 6, 0, col_span=2),
              ProfileElement(goal_field, 7, 0, margins=Margins(left=15)),
              ProfileElement(internal_goal_field, 7, 1, margins=Margins(left=10)),
              ProfileElement(arrow_field(), 8, 0),
              ProfileElement(internal_arrow_field(), 8, 1),
              ProfileElement(motivation_field, 9, 0, margins=Margins(left=15)),
              ProfileElement(internal_motivation_field, 9, 1, margins=Margins(left=10)),
              ProfileElement(arrow_field(), 10, 0),
              ProfileElement(internal_arrow_field(), 10, 1),
              ProfileElement(conflict_field, 11, 0, margins=Margins(left=15)),
              ProfileElement(internal_conflict_field, 11, 1, margins=Margins(left=10)),
              ProfileElement(arrow_field(), 12, 0),
              ProfileElement(internal_arrow_field(), 12, 1),
              ProfileElement(stakes_field, 13, 0, margins=Margins(left=15)),
              ProfileElement(internal_stakes_field, 13, 1, margins=Margins(left=10)),
              ProfileElement(story_title, 14, 0, col_span=2),
              ProfileElement(need_field, 15, 0, col_span=2, margins=Margins(left=15)),
              ProfileElement(weaknesses_field, 16, 0, col_span=2, margins=Margins(left=15)),
              ProfileElement(ghost_field, 17, 0, col_span=2, margins=Margins(left=15)),
              ProfileElement(values_field, 18, 0, col_span=2, margins=Margins(left=15))
              ]
    return [ProfileTemplate(title='Default character template',
                            id=uuid.UUID('6e89c683-c132-469b-a75c-6712af7c339d'),
                            elements=fields)]


entity_summary_field = TemplateField('Summary', type=TemplateFieldType.SMALL_TEXT,
                                     id=uuid.UUID('207053e6-dd51-4956-8830-478fe8efca0a'),
                                     placeholder="Summarize your entity",
                                     show_label=False)

sight_field = TemplateField('Sight', type=TemplateFieldType.SMALL_TEXT,
                            id=uuid.UUID('935e6595-27ae-426e-8b41-b315e9160ad9'),
                            emoji=':eyes:',
                            show_label=False,
                            placeholder='Sight')

smell_field = TemplateField('Smell', type=TemplateFieldType.SMALL_TEXT,
                            id=uuid.UUID('50245a33-599b-49c6-9746-094f12b4d667'),
                            emoji=':pig_nose:',
                            show_label=False,
                            placeholder='Smell')
noise_field = TemplateField('Sound', type=TemplateFieldType.SMALL_TEXT,
                            id=uuid.UUID('76659d94-8753-4945-8d5c-e811189e3b49'),
                            emoji=':bell:',
                            show_label=False,
                            placeholder='Sound')

animals_field = TemplateField('Animals', type=TemplateFieldType.LABELS,
                              id=uuid.UUID('3aa9cc09-312c-492a-bc19-6914bb1eeba6'),
                              emoji=':paw_prints:',
                              show_label=False,
                              placeholder='Animals')
nature_field = TemplateField('Nature', type=TemplateFieldType.LABELS,
                             id=uuid.UUID('ab54bf84-1b69-4bb4-b1b4-c04ad2dd58b1'),
                             emoji=':shamrock:',
                             placeholder='Nature')


def default_location_profiles() -> List[ProfileTemplate]:
    summary_title = TemplateField('Summary', type=TemplateFieldType.DISPLAY_HEADER, required=True)
    sensory_title = TemplateField('Sensory details', type=TemplateFieldType.DISPLAY_HEADER, required=True)
    fields = [
        ProfileElement(summary_title, 0, 0),
        ProfileElement(entity_summary_field, 1, 0, margins=Margins(left=15)),
        ProfileElement(sensory_title, 2, 0),
        ProfileElement(sight_field, 3, 0, margins=Margins(left=15)),
        ProfileElement(smell_field, 4, 0, margins=Margins(left=15)),
        ProfileElement(noise_field, 5, 0, margins=Margins(left=15)),
    ]
    return [ProfileTemplate(title='Default location template',
                            id=uuid.UUID('8a95aa51-a975-416e-83d4-e349b84565b1'),
                            elements=fields)]
