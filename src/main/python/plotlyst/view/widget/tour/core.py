"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
import copy
import uuid
from dataclasses import dataclass
from enum import Enum, auto
from typing import List

from PyQt6.QtCore import QObject

from plotlyst.core.domain import Novel, three_act_structure, Document
from plotlyst.event.core import Event


# flake8: noqa
class Tutorial(Enum):
    ContainerIntroduction = auto()
    FirstNovel = auto()
    FirstCharacter = auto()
    FirstScene = auto()
    FirstProtagonist = auto()

    def is_container(self) -> bool:
        return self.name.startswith('Container')


COLOR_ON_NAVBAR: str = '#e9c46a'


@dataclass
class TourEvent(Event):
    message: str = ''
    action: str = ''
    delegate_click: bool = True


first_scene = Novel.new_scene('First scene')
first_scene.manuscript = Document('')
first_scene.manuscript.loaded = True

tutorial_novel = Novel('My new novel', id=uuid.UUID('a1a88622-4612-4c90-9848-8ef93b423bda'),
                       story_structures=[copy.deepcopy(three_act_structure)],
                       tutorial=True,
                       scenes=[first_scene])
tutorial_novel.story_structures[0].active = True


class LibraryTourEvent(TourEvent):
    pass


class NewStoryButtonTourEvent(TourEvent):
    pass


# shows the dialog without hijacking the main eventloop
class NewStoryDialogOpenTourEvent(TourEvent):
    pass


class NewStoryTitleInDialogTourEvent(TourEvent):
    pass


@dataclass
class NewStoryTitleFillInDialogTourEvent(TourEvent):
    title: str = ''


class NewStoryDialogWizardCustomizationTourEvent(TourEvent):
    pass


class NewStoryDialogOkayButtonTourEvent(TourEvent):
    pass


class TutorialNovelSelectTourEvent(TourEvent):
    pass


class NovelDisplayTourEvent(TourEvent):
    pass


class NovelEditorDisplayTourEvent(TourEvent):
    pass


class NovelOpenButtonTourEvent(TourEvent):
    pass


class TutorialNovelOpenTourEvent(TourEvent):
    pass


class TutorialNovelCloseTourEvent(TourEvent):
    pass


class NovelTopLevelButtonTourEvent(TourEvent):
    pass


class HomeTopLevelButtonTourEvent(TourEvent):
    pass


class AllNovelViewsTourEvent(TourEvent):
    pass


@dataclass
class BaseNovelViewTourEvent(TourEvent):
    click_before: bool = False


class GeneralNovelViewTourEvent(BaseNovelViewTourEvent):
    pass


class CharacterViewTourEvent(BaseNovelViewTourEvent):
    pass


class ScenesViewTourEvent(BaseNovelViewTourEvent):
    pass


class DocumentsViewTourEvent(BaseNovelViewTourEvent):
    pass


class ManuscriptViewTourEvent(BaseNovelViewTourEvent):
    pass


class AnalysisViewTourEvent(BaseNovelViewTourEvent):
    pass


class BoardViewTourEvent(BaseNovelViewTourEvent):
    pass


class CharacterNewButtonTourEvent(TourEvent):
    pass


class CharacterCardTourEvent(TourEvent):
    pass


class CharacterPerspectivesTourEvent(TourEvent):
    pass


@dataclass
class BasePerspectiveTourEvent(TourEvent):
    click_before: bool = False


class CharacterPerspectiveCardsTourEvent(BasePerspectiveTourEvent):
    pass


class CharacterPerspectiveTableTourEvent(BasePerspectiveTourEvent):
    pass


class CharacterPerspectiveComparisonTourEvent(BasePerspectiveTourEvent):
    pass


class CharacterPerspectiveNetworkTourEvent(BasePerspectiveTourEvent):
    pass


class CharacterPerspectiveProgressTourEvent(BasePerspectiveTourEvent):
    pass


class CharacterDisplayTourEvent(TourEvent):
    pass


class CharacterEditorTourEvent(TourEvent):
    pass


class CharacterEditorNameLineEditTourEvent(TourEvent):
    pass


@dataclass
class CharacterEditorNameFilledTourEvent(TourEvent):
    name: str = ''


class CharacterEditorAvatarDisplayTourEvent(TourEvent):
    pass


class CharacterEditorAvatarMenuTourEvent(TourEvent):
    pass


class CharacterEditorAvatarMenuCloseTourEvent(TourEvent):
    pass


class CharacterEditorBackButtonTourEvent(TourEvent):
    pass


def tour_events(tutorial: Tutorial, sender: QObject):
    return tour_factories[tutorial](sender)


def first_novel_tour_factory(sender: QObject) -> List[TourEvent]:
    return [LibraryTourEvent(sender,
                             message='Navigate first to your library panel. This is where you will find all your stories.'),
            NewStoryButtonTourEvent(sender, delegate_click=False),
            NewStoryDialogOpenTourEvent(sender),
            NewStoryTitleInDialogTourEvent(sender,
                                           message="Specify your story's name. You can change it later. Now click to autofill.",
                                           action='Fill in',
                                           delegate_click=False),
            NewStoryTitleFillInDialogTourEvent(sender, title='My new novel'),
            NewStoryDialogWizardCustomizationTourEvent(sender,
                                                       message="A personalization step is available to help you customzie your experience. Let's turn this off, for now."),
            NewStoryDialogOkayButtonTourEvent(sender),
            TutorialNovelSelectTourEvent(sender),
            NovelDisplayTourEvent(sender,
                                  message="This is your novel's main display. You can edit the title or subtitle here.",
                                  delegate_click=False, action='Next'),
            NovelOpenButtonTourEvent(sender, message="Let's open your new novel to start working on it.",
                                     delegate_click=False),
            TutorialNovelOpenTourEvent(sender),
            NovelTopLevelButtonTourEvent(sender,
                                         message="A new page appeared for your novel", delegate_click=False,
                                         action='Next'),
            NovelEditorDisplayTourEvent(sender, message="This is your novel editor", delegate_click=False,
                                        action='Next'),
            AllNovelViewsTourEvent(sender, message="There are different panels you can navigate through",
                                   delegate_click=False, action='Next'),
            GeneralNovelViewTourEvent(sender, message="Overall story elements, e.g., structure and plot"),
            CharacterViewTourEvent(sender, message="Characters", click_before=True),
            ScenesViewTourEvent(sender, message="Scenes and chapters", click_before=True),
            ManuscriptViewTourEvent(sender, message="Manuscript panel where you can write your story",
                                    click_before=True),
            DocumentsViewTourEvent(sender, message="General research and documents", click_before=True),
            AnalysisViewTourEvent(sender, message="Analysis panel that offers different reports", click_before=True),
            BoardViewTourEvent(sender, message="A task management panel where you can remain organized",
                               click_before=True),
            NovelTopLevelButtonTourEvent(sender,
                                         message="You can switch between your novel editor and the home panel in the top.",
                                         action='Next'),
            HomeTopLevelButtonTourEvent(sender),
            NovelDisplayTourEvent(sender, message="The tour is over! Check out more tutorials to learn about Plotlyst!",
                                  delegate_click=False,
                                  action='Finish tour')]


def first_character_tour_factory(sender: QObject) -> List[TourEvent]:
    return [
        TutorialNovelOpenTourEvent(sender),
        CharacterViewTourEvent(sender, message="Visit the Characters panel"),
        CharacterNewButtonTourEvent(sender, message='Click to add a new character'),
        CharacterEditorTourEvent(sender,
                                 message='This your character editor panel. You can edit character role, personality, backstory, etc.',
                                 action='Next'),
        CharacterEditorNameLineEditTourEvent(sender, message="Let's give the character a name",
                                             action="Name her 'Jane'"),
        CharacterEditorNameFilledTourEvent(sender, name='Jane'),
        CharacterEditorNameLineEditTourEvent(sender, message="Good. That is your character's name.", action='Next'),
        CharacterEditorAvatarDisplayTourEvent(sender,
                                              message="Notice how the character's avatar changed. Click to customize it more."),
        CharacterEditorAvatarMenuTourEvent(sender,
                                           message="Multiple options are available for a character's avatar. To get the most out of Plotlyst, we recommend uploading custom images",
                                           action='Next'),
        CharacterEditorAvatarMenuCloseTourEvent(sender),
        CharacterEditorBackButtonTourEvent(sender, message="Let's close the character editor for now and go back "),
        CharacterCardTourEvent(sender, message='A character card was created for your new character', action='Next',
                               delegate_click=False),
        CharacterPerspectivesTourEvent(sender,
                                       message='Multiple perspectives are available to offer different views for the characters',
                                       action='Next', delegate_click=False),
        CharacterPerspectiveCardsTourEvent(sender, message='Display all characters in a card view', click_before=True),
        CharacterPerspectiveTableTourEvent(sender, message='Display all characters in a table', click_before=True),
        CharacterPerspectiveComparisonTourEvent(sender, 'Compare characters to each other by certain attributes',
                                                click_before=True),
        CharacterPerspectiveNetworkTourEvent(sender, 'Visualize a relationship network among your characters',
                                             click_before=True),
        CharacterPerspectiveProgressTourEvent(sender, 'Track the progress of your character profiles',
                                              click_before=True),
        CharacterDisplayTourEvent(sender, 'The tour is over! Check out more tutorials to learn about characters.',
                                  action='Finish tour')
    ]


tour_factories = {
    Tutorial.FirstNovel: first_novel_tour_factory,
    Tutorial.FirstCharacter: first_character_tour_factory,
}
tour_teardowns = {Tutorial.FirstNovel: TutorialNovelCloseTourEvent}
