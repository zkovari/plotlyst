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

import pytest

from src.main.python.plotlyst.core.client import context, client
from src.main.python.plotlyst.core.domain import Character, StoryLine, Scene, Chapter
from src.main.python.plotlyst.view.main_window import MainWindow
from src.main.python.plotlyst.view.stylesheet import APP_STYLESHEET


@pytest.fixture
def test_client(tmp_path):
    context.init(tmp_path)


@pytest.fixture
def in_memory_test_client():
    context.init(':memory:')


@pytest.fixture
def window(qtbot, in_memory_test_client):
    return get_main_window(qtbot)


@pytest.fixture
def window_with_disk_db(qtbot, test_client):
    return get_main_window(qtbot)


def get_main_window(qtbot):
    main_window = MainWindow()
    main_window.setStyleSheet(APP_STYLESHEET)
    main_window.show()
    qtbot.addWidget(main_window)
    qtbot.waitExposed(main_window, timeout=5000)

    return main_window


@pytest.fixture
def filled_window(qtbot, in_memory_test_client):
    novel = client.novels()[0]
    char_a = Character(name='Alfred')
    char_b = Character(name='Babel')
    char_c = Character(name='Celine')
    char_d = Character(name='Delphine')
    char_e = Character(name='Edward')
    client.insert_character(novel, char_a)
    client.insert_character(novel, char_b)
    client.insert_character(novel, char_c)
    client.insert_character(novel, char_d)
    client.insert_character(novel, char_e)

    storyline_main = StoryLine(text='Main')
    storyline_lesser = StoryLine(text='Lesser')
    storyline_love = StoryLine(text='Love')
    client.insert_story_line(novel, storyline_main)
    client.insert_story_line(novel, storyline_lesser)
    client.insert_story_line(novel, storyline_love)

    chapter_1 = Chapter(title='1', sequence=0)
    chapter_2 = Chapter(title='2', sequence=1)
    client.insert_chapter(novel, chapter_1)
    client.insert_chapter(novel, chapter_2)
    scene_1 = Scene(title='Scene 1', synopsis='Scene 1 synopsis', pov=char_a, characters=[char_b, char_c],
                    story_lines=[storyline_main], sequence=0, chapter=chapter_1, day=1)
    scene_2 = Scene(title='Scene 2', synopsis='Scene 2 synopsis', pov=char_d, characters=[char_c, char_a],
                    story_lines=[storyline_lesser, storyline_love], sequence=1, chapter=chapter_2, day=2)
    client.insert_scene(novel, scene_1)
    client.update_scene_chapter(scene_1)
    client.insert_scene(novel, scene_2)
    client.update_scene_chapter(scene_2)

    main_window = MainWindow()
    main_window.setStyleSheet(APP_STYLESHEET)
    main_window.show()
    qtbot.addWidget(main_window)
    qtbot.waitExposed(main_window, timeout=5000)

    return main_window
