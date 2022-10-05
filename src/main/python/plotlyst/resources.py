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
from dataclasses import dataclass

from fbs_runtime.application_context.PyQt6 import ApplicationContext


class ResourceRegistry:

    def __init__(self):
        self._cork = None
        self._frame1 = None
        self._cover1 = None
        self._banner = None
        self._circular_frame1 = None

    def set_up(self, app_context: ApplicationContext):
        self._cork = app_context.get_resource('cork.wav')
        self._frame1 = app_context.get_resource('frame_1.png')
        self._cover1 = app_context.get_resource('cover_1.jpg')
        self._banner = app_context.get_resource('plotlyst_banner.jpg')
        self._circular_frame1 = app_context.get_resource('circular_frame1.png')

    @property
    def cork(self):
        return self._cork

    @property
    def frame1(self):
        return self._frame1

    @property
    def cover1(self):
        return self._cover1

    @property
    def banner(self):
        return self._banner

    @property
    def circular_frame1(self):
        return self._circular_frame1


resource_registry = ResourceRegistry()


@dataclass
class NltkResource:
    name: str
    folder: str
    web_url: str


punkt_nltk_resource = NltkResource('punkt', 'tokenizers',
                                   'https://github.com/nltk/nltk_data/raw/gh-pages/packages/tokenizers/punkt.zip')
avg_tagger_url = 'https://github.com/nltk/nltk_data/raw/gh-pages/packages/taggers/averaged_perceptron_tagger.zip'
avg_tagger_nltk_resource = NltkResource('averaged_perceptron_tagger', 'taggers', avg_tagger_url)


class ResourceManager:
    def has_nltk_resource(self) -> bool:
        pass
