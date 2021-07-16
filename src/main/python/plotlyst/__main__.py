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
import os
import subprocess
import sys
import traceback

try:
    from PyQt5 import QtWidgets, QtGui
    from PyQt5.QtCore import QCoreApplication, QSettings, Qt
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import QFileDialog, QApplication, QMessageBox
    from fbs_runtime.application_context.PyQt5 import ApplicationContext

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
    while True:
        app = appctxt.app
        font = QFont('Noto Sans')
        QApplication.setFont(font)
        QCoreApplication.setOrganizationName('CraftOfGem')
        QCoreApplication.setOrganizationDomain('craftofgem.com')
        QCoreApplication.setApplicationName('NovelApp')

        settings = QSettings()
        db_file = settings.value('workspace')

        if not db_file:
            dir = QFileDialog.getExistingDirectory(None, 'Choose directory')
            db_file = os.path.join(dir, 'novels.sqlite')
            settings.setValue('workspace', db_file)
        try:
            context.init(db_file)
        except Exception as ex:
            QMessageBox.critical(None, 'Could not initialize database', traceback.format_exc())
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
