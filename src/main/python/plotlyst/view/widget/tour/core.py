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

from src.main.python.plotlyst.event.core import Event


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


class LibraryTourEvent(TourEvent):
    pass
