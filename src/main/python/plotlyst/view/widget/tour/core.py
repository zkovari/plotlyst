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
from dataclasses import dataclass
from enum import Enum
from typing import List

from PyQt6.QtCore import QObject

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


class LibraryTourEvent(TourEvent):
    pass


class NewStoryButtonTourEvent(TourEvent):
    pass


# shows the dialog without hijacking the main eventloop
class NewStoryDialogOpenTourEvent(TourEvent):
    pass


class NewStoryTitleInDialogTourEvent(TourEvent):
    pass


class NewStoryTitleFillInDialogTourEvent(TourEvent):
    title: str


def tour_events(tutorial: Tutorial, sender: QObject):
    return tour_factories[tutorial](sender)


def first_novel_tour_factory(sender: QObject) -> List[TourEvent]:
    return [LibraryTourEvent(sender,
                             message='Navigate first to your library panel. This is where you will find all your stories.'),
            NewStoryButtonTourEvent(sender, message="Let's create a new story.", delegate_click=False),
            NewStoryDialogOpenTourEvent(sender),
            NewStoryTitleInDialogTourEvent(sender,
                                           message="Specify your story's name. You can change it later. Now click the button to autofill.",
                                           action='Fill in',
                                           delegate_click=False)]


tour_factories = {Tutorial.FirstNovel: first_novel_tour_factory}
