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
import traceback
from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict

from PyQt5.QtCore import QObject, pyqtSignal
from overrides import overrides
from peewee import SqliteDatabase

from src.main.python.plotlyst.core.client import ApplicationModel, ApplicationDbVersion, LATEST


@dataclass
class DatabaseVersion:
    up_to_date: bool
    revision: ApplicationDbVersion


def is_up_to_date() -> DatabaseVersion:
    if not ApplicationModel.table_exists():
        return DatabaseVersion(False, ApplicationDbVersion.R0)

    model: ApplicationModel = ApplicationModel.get_by_id(1)
    if model.revision == LATEST.value:
        return DatabaseVersion(True, LATEST)
    else:
        return DatabaseVersion(False, ApplicationDbVersion[model.revision])


class _MigrationHandler:

    @abstractmethod
    def migrate(self, db: SqliteDatabase):
        pass

    @abstractmethod
    def verify(self, db: SqliteDatabase) -> bool:
        pass


class _R1MigrationHandler(_MigrationHandler):

    @overrides
    def migrate(self, db: SqliteDatabase):
        db.create_tables([ApplicationModel])
        ApplicationModel.create(revision=ApplicationDbVersion.R1.value)

    @overrides
    def verify(self, db: SqliteDatabase) -> bool:
        if not ApplicationModel.table_exists():
            return False

        model: ApplicationModel = ApplicationModel.get_by_id(1)
        return model.revision == LATEST.value


class Migration(QObject):
    stepFinished = pyqtSignal(ApplicationDbVersion)
    migrationFailed = pyqtSignal(str)
    migrationFinished = pyqtSignal()

    def __init__(self, parent=None):
        super(Migration, self).__init__(parent)
        self._migrations: Dict[ApplicationDbVersion, _MigrationHandler] = {
            ApplicationDbVersion.R1: _R1MigrationHandler()}

    def migrate(self, db: SqliteDatabase, version: DatabaseVersion):
        revision: int = version.revision.value
        revision += 1
        while revision <= LATEST.value:
            handler = self._migrations[ApplicationDbVersion(revision)]
            try:
                handler.migrate(db)
                if not handler.verify(db):
                    self.migrationFailed.emit(f'Migration verification failed at step {revision}')
                    return
            except Exception:
                self.migrationFailed.emit(f'Migration failed for revision {revision}: {traceback.format_exc()}')
                return
            self.stepFinished.emit(ApplicationDbVersion(revision))
            revision += 1
        self.migrationFinished.emit()
