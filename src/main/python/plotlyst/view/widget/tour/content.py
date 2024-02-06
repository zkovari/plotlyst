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
from typing import Dict

from plotlyst.view.widget.tour import Tutorial

# flake8: noqa
tutorial_titles: Dict[Tutorial, str] = {
    Tutorial.FirstNovel: 'Create your first novel',
    Tutorial.FirstCharacter: 'Create your first character',
    Tutorial.FirstScene: 'Create your first scene',
    Tutorial.FirstProtagonist: 'Create your first protagonist',
}

tutorial_descriptions: Dict[Tutorial, str] = {
    Tutorial.FirstNovel: '''In this tutorial, you will create your first novel. You will:
 * Use the Library panel to create a novel
 * Open the created novel and navigate through its primary panels, e.g., characters, scenes, manuscript, etc.
''',
    Tutorial.FirstCharacter: '''Let's create your first character. You will:
 * Add a new character and give them a name
 * Select an avatar
 * Browse the different perspectives that include your new character
    '''
}
