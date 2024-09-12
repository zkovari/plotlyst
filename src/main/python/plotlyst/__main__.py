"""
Plotlyst
Copyright (C) 2021-2024  Zsolt Kovari

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
import logging

from plotlyst.service.log import setup_logging

try:
    import argparse
    import os
    import subprocess
    import sys
    import traceback
    from typing import Optional

    from overrides import overrides

    from plotlyst.env import AppMode, app_env
    from plotlyst.resources import resource_registry, resource_manager
    from plotlyst.settings import settings
    from plotlyst.service.persistence import flush_or_fail
    from plotlyst.service.dir import select_new_project_directory, default_directory

    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from fbs_runtime.application_context.PyQt6 import ApplicationContext
    from fbs_runtime import platform
    from fbs_runtime.application_context import cached_property, is_frozen

    from plotlyst.core.client import json_client
    from plotlyst.event.handler import DialogExceptionHandler
    from plotlyst.view.main_window import MainWindow
    from plotlyst.view.stylesheet import APP_STYLESHEET
except Exception as ex:
    appctxt = ApplicationContext()
    QMessageBox.critical(None, 'Could not launch application', traceback.format_exc())
    raise ex


class AppContext(ApplicationContext):

    @overrides
    def run(self):
        pass

    @cached_property
    def exception_handlers(self):
        result = super().exception_handlers
        result.append(self.dialog_exception_handler)
        return result

    @cached_property
    def app(self):
        result = self._qt_binding.QApplication([])
        result.setApplicationName('Plotlyst')
        result.setApplicationVersion('0.1.0')
        return result

    @cached_property
    def dialog_exception_handler(self):
        return DialogExceptionHandler()


if __name__ == '__main__':
    if app_env.is_windows():
        app = QApplication(sys.argv)
        appctxt = None
    else:
        appctxt = AppContext()
        app = appctxt.app

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=lambda mode: AppMode[mode.upper()], choices=list(AppMode), default=AppMode.PROD)
    parser.add_argument('--clear', action='store_true')
    args = parser.parse_args()
    app_env.mode = args.mode

    setup_logging()

    if platform.is_linux():
        font = QFont('Helvetica', max(QApplication.font().pointSize(), 12))
        logging.info(f'Linux OS was detected. Set font to Helvetica, {font.pointSize()}pt')
        QApplication.setFont(font)
    elif QApplication.font().pointSize() < 12:
        font = QApplication.font()
        font.setPointSize(12)
        QApplication.setFont(font)
    app.setStyleSheet(APP_STYLESHEET)
    settings.init_org()
    if args.clear:
        settings.clear()
    resource_registry.set_up(appctxt)
    resource_manager.init()
    workspace: Optional[str] = settings.workspace()
    if not workspace or not os.path.exists(workspace):
        workspace = default_directory()
    changed_dir = False
    while True:
        if not workspace:
            workspace = select_new_project_directory()
        if workspace:
            settings.set_workspace(workspace)
            break
    try:
        json_client.init(workspace)
    except Exception as ex:
        QMessageBox.critical(None, 'Could not initialize database', traceback.format_exc())
        raise ex
    try:
        window = MainWindow()
    except Exception as ex:
        QMessageBox.critical(None, 'Could not create main window', traceback.format_exc())
        raise ex
    window.show()
    window.activateWindow()
    # first_launch = settings.first_launch()
    # if first_launch:
    #     QTimer.singleShot(1000, AboutDialog.popup)
    #     settings.set_launched_before()
    sys.exit(app.exec_())
