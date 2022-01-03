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


class AppMode(Enum):
    DEV = 0
    PROD = 1


class AppEnvironment:
    def __init__(self):
        self._mode: AppMode = AppMode.PROD

    @property
    def mode(self) -> AppMode:
        return self._mode

    @mode.setter
    def mode(self, value: AppMode):
        self._mode = value

    def is_dev(self) -> bool:
        return self._mode == AppMode.DEV

    def is_prod(self) -> bool:
        return self._mode == AppMode.PROD

    def test_env(self) -> bool:
        if os.getenv('PLOTLYST_TEST_ENV'):
            return True
        return False


app_env = AppEnvironment()
