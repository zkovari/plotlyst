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
import argparse
import os
import subprocess
import sys
import traceback
from typing import Optional

from src.main.python.plotlyst.env import AppMode, app_env

try:
    from PyQt5 import QtWidgets, QtGui
    from PyQt5.QtCore import QCoreApplication, QSettings, Qt
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import QFileDialog, QApplication, QMessageBox
    from fbs_runtime.application_context.PyQt5 import ApplicationContext

    from src.main.python.plotlyst.core.migration import app_db_schema_version, AppDbSchemaVersion
    from src.main.python.plotlyst.view.dialog.migration import MigrationDialog
    from src.main.python.plotlyst.common import EXIT_CODE_RESTART
    from src.main.python.plotlyst.core.client import context
    from src.main.python.plotlyst.event.handler import exception_handler
    from src.main.python.plotlyst.view.dialog.about import AboutDialog
    from src.main.python.plotlyst.view.main_window import MainWindow
    from src.main.python.plotlyst.view.stylesheet import APP_STYLESHEET
except Exception as ex:
    appctxt = ApplicationContext()
    QMessageBox.critical(None, 'Could not launch application', traceback.format_exc())
    raise ex

QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons

if __name__ == '__main__':
    appctxt = ApplicationContext()

    QtGui.QFontDatabase.addApplicationFont(appctxt.get_resource('NotoColorEmoji.ttf'))
    QtGui.QFontDatabase.addApplicationFont(appctxt.get_resource('NotoSans-Light.ttf'))

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=lambda mode: AppMode[mode.upper()], choices=list(AppMode), default=AppMode.PROD)
    args = parser.parse_args()
    app_env.mode = args.mode
    while True:
        app = appctxt.app
        font = QFont('Noto Sans')
        QApplication.setFont(font)
        QCoreApplication.setOrganizationName('CraftOfGem')
        QCoreApplication.setOrganizationDomain('craftofgem.com')
        QCoreApplication.setApplicationName('NovelApp')

        settings = QSettings()
        workspace: Optional[str] = settings.value('workspace')

        changed_dir = False
        while True:
            if not workspace:
                workspace = QFileDialog.getExistingDirectory(None, 'Choose directory')
                changed_dir = True

            if not os.path.exists(workspace):
                QMessageBox.warning(None, 'Invalid project directory',
                                    f"The chosen directory doesn't exist: {workspace}")
            elif os.path.isfile(workspace):
                QMessageBox.warning(None, 'Invalid project directory',
                                    f"The chosen path should be a directory, not a file: {workspace}")
            elif not os.access(workspace, os.W_OK):
                QMessageBox.warning(None, 'Invalid project directory',
                                    f"The chosen directory cannot be written: {workspace}")
            else:
                if changed_dir:
                    settings.setValue('workspace', workspace)
                break
            workspace = None

        try:
            context.init(workspace)
        except Exception as ex:
            QMessageBox.critical(None, 'Could not initialize database', traceback.format_exc())
            raise ex

        try:
            version: AppDbSchemaVersion = app_db_schema_version()
            if not version.up_to_date:
                migration_diag = MigrationDialog(version)
                if not migration_diag.display():
                    exit(1)
        except Exception as ex:
            QMessageBox.critical(None, 'Could not finish database migration', traceback.format_exc())
            raise ex

        try:
            window = MainWindow()
        except Exception as ex:
            QMessageBox.critical(None, 'Could not create main window', traceback.format_exc())
            raise ex
        app.setStyleSheet(APP_STYLESHEET)

        window.show()
        window.activateWindow()

        launched_before = settings.value('launchedBefore', False)
        if not launched_before:
            AboutDialog().exec()
            settings.setValue('launchedBefore', True)

        sys.excepthook = exception_handler  # type: ignore
        exit_code = appctxt.app.exec_()
        if exit_code < EXIT_CODE_RESTART:
            break

        # restart process
        subprocess.call('./gen.sh')
        python = sys.executable
        os.execl(python, python, *sys.argv)
