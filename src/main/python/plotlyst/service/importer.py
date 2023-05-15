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

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QIcon
from overrides import overrides
from qthandy import busy

from src.main.python.plotlyst.core.domain import Novel
from src.main.python.plotlyst.core.scrivener import ScrivenerParser
from src.main.python.plotlyst.service.persistence import RepositoryPersistenceManager, flush_or_fail
from src.main.python.plotlyst.view.icons import IconRegistry


class SyncImporter(QObject):

    def __init__(self):
        super(SyncImporter, self).__init__()
        self._parser = ScrivenerParser()
        self.repo = RepositoryPersistenceManager.instance()

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
        path_ = Path(novel.import_origin.source)
        return path_.exists() and path_.is_dir()

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
    def location_exists(self, novel: Novel) -> bool:
        exists = super(ScrivenerSyncImporter, self).location_exists(novel)

        if exists:
            scriv_file = self._parser.find_scrivener_file(novel.import_origin.source)
            if not scriv_file:
                print('scriv file not found')
                return False

        return exists

    @overrides
    def is_updated(self, novel: Novel) -> bool:
        return self._mod_time(novel) == novel.import_origin.last_mod_time

    @overrides
    def change_location(self, novel: Novel):
        pass

    @busy
    def sync(self, novel: Novel):
        novel.import_origin.last_mod_time = self._mod_time(novel)

        new_novel = self._parser.parse_project(novel.import_origin.source)
        flush_or_fail()

        self._sync_characters(novel, new_novel)
        self._sync_chapters(novel, new_novel)
        self._sync_scenes(novel, new_novel)

        self.repo.update_project_novel(novel)

    def _mod_time(self, novel: Novel) -> int:
        scriv_file = self._parser.find_scrivener_file(novel.import_origin.source)
        return Path(novel.import_origin.source).joinpath(scriv_file).stat().st_mtime_ns

    def _sync_characters(self, novel: Novel, new_novel: Novel):
        pass
    
    def _sync_chapters(self, novel: Novel, new_novel: Novel):
        self.repo.update_novel(novel)

    def _sync_scenes(self, novel: Novel, new_novel: Novel):
        pass
