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
from typing import Dict

from src.main.python.plotlyst.view.widget.tour import Tutorial

# flake8: noqa
tutorial_titles: Dict[Tutorial, str] = {
    Tutorial.FirstNovel: 'Create your first novel',
    Tutorial.FirstScene: 'Create your first scene',
    Tutorial.FirstProtagonist: 'Create your first protagonist',
}

tutorial_descriptions: Dict[Tutorial, str] = {}

tutorial_descriptions[Tutorial.FirstNovel] = '''In this tutorial, you will create your first novel. You will learn how to:
 * Use the Library panel to create and edit novels
 * Open the corresponding novel editor to navigate through the different story panels, e.g., characters, scenes, manuscript, etc.
'''
