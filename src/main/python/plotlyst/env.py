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
import os
from enum import Enum
from typing import Optional

from fbs_runtime import platform

from src.main.python.plotlyst.core.domain import Novel


class AppMode(Enum):
    DEV = 0
    PROD = 1


class AppEnvironment:
    def __init__(self):
        self._mode: AppMode = AppMode.PROD
        self._novel: Optional[Novel] = None
        self._plotlyst_cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'plotlyst')
        self._nltk_data = os.path.join(self._plotlyst_cache_dir, 'nltk')
        os.environ['NLTK_DATA'] = self._nltk_data
        os.environ['LTP_PATH'] = os.path.join(self._plotlyst_cache_dir, 'language_tool_python')

    @property
    def mode(self) -> AppMode:
        return self._mode

    @mode.setter
    def mode(self, value: AppMode):
        self._mode = value

    @property
    def novel(self):
        return self._novel

    @novel.setter
    def novel(self, novel: Novel):
        self._novel = novel

    @property
    def nltk_data(self) -> str:
        return self._nltk_data

    def is_dev(self) -> bool:
        return self._mode == AppMode.DEV

    def is_prod(self) -> bool:
        return self._mode == AppMode.PROD

    def test_env(self) -> bool:
        if os.getenv('PLOTLYST_TEST_ENV'):
            return True
        return False

    def is_mac(self) -> bool:
        return platform.is_mac()

    def is_linux(self) -> bool:
        return platform.is_linux()

    def is_windows(self) -> bool:
        return platform.is_windows()


app_env = AppEnvironment()
