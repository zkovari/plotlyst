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
from typing import List, Optional

from src.main.python.plotlyst.core.domain import SceneBuilderElement, SceneBuilderElementType


class TextBuilder:
    sentence_end_characters = ['.', '?', '!', '"', "'", '-']

    def __init__(self):
        self.text: str = ''
        self._last_is_nl: bool = True

    def nl(self):
        if not self.text:
            return
        self.text += '\n'
        self._last_is_nl = True

    def append(self, text: str):
        new_text = text.strip()
        if not new_text:
            return
        if new_text[-1] not in self.sentence_end_characters:
            new_text += '.'
        if not self._last_is_nl:
            self.text += ' '
        self.text += new_text

        self._last_is_nl = False


def generate_text_from_scene_builder(elements: List[SceneBuilderElement]) -> str:
    text_builder = TextBuilder()
    for el in elements:
        _parse_to_text(el, text_builder)
    return text_builder.text


def _parse_to_text(el: SceneBuilderElement, text: TextBuilder, previous: Optional[SceneBuilderElement] = None):
    if el.type == SceneBuilderElementType.CHARACTER_ENTRY:
        text.nl()
        text.append(f'{el.character.name} enters the scene.')
        if el.text:
            text.append(el.text)
    elif el.type == SceneBuilderElementType.REACTION:
        text.nl()
    elif el.type in [SceneBuilderElementType.REFLEX, SceneBuilderElementType.FEELING, SceneBuilderElementType.MONOLOG]:
        text.append(el.text)
    elif el.type == SceneBuilderElementType.SPEECH:
        text.nl()
        text.append(f'"{el.text}"')
    elif el.type == SceneBuilderElementType.ACTION_BEAT:
        text.append(el.text)
    else:
        text.nl()
        text.append(el.text)

    for child in el.children:
        _parse_to_text(child, text, el)
