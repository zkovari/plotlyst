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

try:
    import argparse
    import os
    import subprocess
    import sys
    import traceback
    from typing import Optional

    from overrides import overrides

    from src.main.python.plotlyst.env import AppMode, app_env
    from src.main.python.plotlyst.settings import settings
    from src.main.python.plotlyst.view.dialog.dir import DirectoryPickerDialog

    from PyQt5 import QtWidgets, QtGui
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import QFileDialog, QApplication, QMessageBox, QMainWindow, QComboBox
    from fbs_runtime.application_context.PyQt5 import ApplicationContext
    from fbs_runtime import PUBLIC_SETTINGS
    from fbs_runtime.application_context import cached_property, is_frozen
    from fbs_runtime.excepthook.sentry import SentryExceptionHandler

    from src.main.python.plotlyst.core.migration import app_db_schema_version, AppDbSchemaVersion
    from src.main.python.plotlyst.view.dialog.migration import MigrationDialog
    from src.main.python.plotlyst.common import EXIT_CODE_RESTART
    from src.main.python.plotlyst.core.client import context
    from src.main.python.plotlyst.event.handler import DialogExceptionHandler
    from src.main.python.plotlyst.view.dialog.about import AboutDialog
    from src.main.python.plotlyst.view.main_window import MainWindow
    from src.main.python.plotlyst.view.stylesheet import APP_STYLESHEET
except Exception as ex:
    appctxt = ApplicationContext()
    QMessageBox.critical(None, 'Could not launch application', traceback.format_exc())
    raise ex

QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons


class AppContext(ApplicationContext):

    @overrides
    def run(self):
        pass

    @cached_property
    def exception_handlers(self):
        result = super().exception_handlers
        result.append(self.dialog_exception_handler)
        if is_frozen():
            result.append(self.sentry_exception_handler)
        return result

    @cached_property
    def sentry_exception_handler(self):
        return SentryExceptionHandler(
            PUBLIC_SETTINGS['sentry_dsn'],
            PUBLIC_SETTINGS['version'],
            PUBLIC_SETTINGS['environment'], callback=self._on_sentry_init
        )

    @cached_property
    def dialog_exception_handler(self):
        return DialogExceptionHandler()

    def _on_sentry_init(self):
        scope = self.sentry_exception_handler.scope
        from fbs_runtime import platform
        scope.set_extra('os', platform.name())


if __name__ == '__main__':
    appctxt = AppContext()

    # QtGui.QFontDatabase.addApplicationFont(appctxt.get_resource('NotoColorEmoji.ttf'))
    # QtGui.QFontDatabase.addApplicationFont(appctxt.get_resource('NotoSans-Light.ttf'))

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=lambda mode: AppMode[mode.upper()], choices=list(AppMode), default=AppMode.PROD)
    args = parser.parse_args()
    app_env.mode = args.mode
    while True:
        app = appctxt.app
        # font = QFont('Noto Sans')
        # QApplication.setFont(font)
        # app.setStyleSheet(APP_STYLESHEET)
        # settings.init_org()
        #
        # workspace: Optional[str] = settings.workspace()
        #
        # changed_dir = False
        # while True:
        #     if not workspace:
        #         picker = DirectoryPickerDialog()
        #         picker.display()
        #         workspace = QFileDialog.getExistingDirectory(None, 'Choose directory')
        #         changed_dir = True
        #
        #     if not workspace:
        #         exit(0)
        #
        #     if not os.path.exists(workspace):
        #         QMessageBox.warning(None, 'Invalid project directory',
        #                             f"The chosen directory doesn't exist: {workspace}")
        #     elif os.path.isfile(workspace):
        #         QMessageBox.warning(None, 'Invalid project directory',
        #                             f"The chosen path should be a directory, not a file: {workspace}")
        #     elif not os.access(workspace, os.W_OK):
        #         QMessageBox.warning(None, 'Invalid project directory',
        #                             f"The chosen directory cannot be written: {workspace}")
        #     else:
        #         if changed_dir:
        #             settings.set_workspace(workspace)
        #         break
        #     workspace = None
        #
        # try:
        #     context.init(workspace)
        # except Exception as ex:
        #     QMessageBox.critical(None, 'Could not initialize database', traceback.format_exc())
        #     raise ex
        #
        # try:
        #     version: AppDbSchemaVersion = app_db_schema_version()
        #     if not version.up_to_date:
        #         migration_diag = MigrationDialog(version)
        #         if not migration_diag.display():
        #             exit(1)
        # except Exception as ex:
        #     QMessageBox.critical(None, 'Could not finish database migration', traceback.format_exc())
        #     raise ex

        try:
            window = QMainWindow()
        except Exception as ex:
            QMessageBox.critical(None, 'Could not create main window', traceback.format_exc())
            raise ex

        cb = QComboBox()
        cb.addItem('Test1')
        cb.addItem('Test2')
        cb.addItem('Test3')
        window.setCentralWidget(cb)
        window.show()
        # window.activateWindow()

        # first_launch = settings.first_launch()
        # if first_launch:
        #     AboutDialog().exec()
        #     settings.set_launched_before()

        exit_code = appctxt.app.exec_()
        if exit_code < EXIT_CODE_RESTART:
            break

        # restart process
        subprocess.call('./gen.sh')
        python = sys.executable
        os.execl(python, python, *sys.argv)
