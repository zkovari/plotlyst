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
from abc import abstractmethod
from pathlib import Path

from PyQt6.QtGui import QIcon
from overrides import overrides

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.view.icons import IconRegistry


class SyncImporter:

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def icon(self) -> QIcon:
        pass

    def location(self, novel: Novel) -> str:
        if novel.import_origin is None:
            return ''

        return Path(novel.import_origin.source).name

    def location_exists(self, novel: Novel) -> bool:
        return Path(novel.import_origin.source).exists()

    @abstractmethod
    def is_updated(self, novel: Novel) -> bool:
        return False

    def change_location(self, novel: Novel):
        pass

    @abstractmethod
    def sync(self, novel: Novel):
        pass


class ScrivenerSyncImporter(SyncImporter):

    @overrides
    def name(self) -> str:
        return 'Scrivener'

    @overrides
    def icon(self) -> QIcon:
        return IconRegistry.from_name('mdi.alpha-s-circle-outline', color='#410253')

    @overrides
    def is_updated(self, novel: Novel) -> bool:
        return False

    @overrides
    def change_location(self, novel: Novel):
        pass

    @overrides
    def sync(self, novel: Novel):
        pass


scrivener_sync_importer = ScrivenerSyncImporter()
