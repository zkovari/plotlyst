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
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog

from src.main.python.plotlyst.core.client import context
from src.main.python.plotlyst.core.migration import DatabaseVersion, Migration
from src.main.python.plotlyst.view.generated.db_migration_dialog_ui import Ui_MigrationDialog


class MigrationDialog(QDialog):
    def __init__(self, version: DatabaseVersion, parent=None):
        super(MigrationDialog, self).__init__(parent)
        self.version = version
        self.ui = Ui_MigrationDialog()
        self.ui.setupUi(self)
        self._migration = Migration()
        self._migration.migrationFinished.connect(self._finished)
        self._migration.migrationFailed.connect(self._failed)
        self.ui.btnLaunch.setHidden(True)
        self.ui.btnClose.setHidden(True)
        self.ui.btnClose.clicked.connect(self.reject)
        self.ui.btnLaunch.clicked.connect(self.accept)

        self.ui.textBrowser.setHidden(True)

    def display(self) -> bool:
        QTimer.singleShot(500, self._migrate)
        result = self.exec()
        return result == QDialog.Accepted

    def _migrate(self):
        self._migration.migrate(context.db(), self.version)

    def _finished(self):
        self.ui.btnLaunch.setVisible(True)
        self.ui.textBrowser.setVisible(True)
        self.ui.textBrowser.setText('Migration was finished successfully.')

    def _failed(self, message: str):
        self.ui.btnClose.setVisible(True)
        self.ui.textBrowser.setVisible(True)
        self.ui.textBrowser.setText(message)
