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
import copy
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import List

from PyQt6.QtCore import QObject

from src.main.python.plotlyst.core.domain import Novel, three_act_structure
from src.main.python.plotlyst.event.core import Event


# flake8: noqa
class Tutorial(Enum):
    ContainerBasic = 0
    FirstNovel = 1
    FirstProtagonist = 2
    FirstScene = 3

    def is_container(self) -> bool:
        return self.name.startswith('Container')


COLOR_ON_NAVBAR: str = '#e9c46a'


@dataclass
class TourEvent(Event):
    message: str = ''
    action: str = ''
    delegate_click: bool = True


tutorial_novel = Novel('My new novel', id=uuid.UUID('a1a88622-4612-4c90-9848-8ef93b423bda'),
                       story_structures=[copy.deepcopy(three_act_structure)],
                       tutorial=True)


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


def tour_events(tutorial: Tutorial, sender: QObject):
    return tour_factories[tutorial](sender)


def first_novel_tour_factory(sender: QObject) -> List[TourEvent]:
    return [LibraryTourEvent(sender,
                             message='Navigate first to your library panel. This is where you will find all your stories.'),
            NewStoryButtonTourEvent(sender, message="Let's create a new story.", delegate_click=False),
            NewStoryDialogOpenTourEvent(sender),
            NewStoryTitleInDialogTourEvent(sender,
                                           message="Specify your story's name. You can change it later. Now click to autofill.",
                                           action='Fill in',
                                           delegate_click=False),
            NewStoryTitleFillInDialogTourEvent(sender, title='My new novel'),
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
            DocumentsViewTourEvent(sender, message="General research and documents", click_before=True),
            ManuscriptViewTourEvent(sender, message="Manuscript panel where you can write your story",
                                    click_before=True),
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


tour_factories = {Tutorial.FirstNovel: first_novel_tour_factory}
tour_teardowns = {Tutorial.FirstNovel: TutorialNovelCloseTourEvent}
