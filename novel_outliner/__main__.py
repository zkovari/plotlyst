import os
import subprocess
import sys

from PyQt5.QtCore import QCoreApplication, QSettings
from PyQt5.QtWidgets import QFileDialog
from fbs_runtime.application_context.PyQt5 import ApplicationContext

from novel_outliner.common import EXIT_CODE_RESTART
from novel_outliner.core.client import context
from novel_outliner.event.handler import exception_handler
from novel_outliner.view.main_window import MainWindow
from novel_outliner.view.stylesheet import APP_STYLESHEET

if __name__ == '__main__':
    appctxt = ApplicationContext()
    while True:
        app = appctxt.app

        QCoreApplication.setOrganizationName('CraftOfGem')
        QCoreApplication.setOrganizationDomain('craftofgem.com')
        QCoreApplication.setApplicationName('NovelApp')

        settings = QSettings()
        db_file = settings.value('workspace')

        if not db_file:
            dir = QFileDialog.getExistingDirectory(None, 'Choose directory')
            db_file = os.path.join(dir, 'novels.sqlite')
            settings.setValue('workspace', db_file)
        context.init(db_file)
        window = MainWindow()
        app.setStyleSheet(APP_STYLESHEET)

        window.show()
        window.activateWindow()
        sys.excepthook = exception_handler  # type: ignore
        exit_code = appctxt.app.exec_()
        if exit_code < EXIT_CODE_RESTART:
            break

        # restart process
        subprocess.call('./gen.sh')
        python = sys.executable
        os.execl(python, python, *sys.argv)
